"""
This script creates pretty animation on the programmable christmas star.
It works as follows:
 - Define the animation parameters at the top of the file
 - The script then calculates the x,y coordinates of the LEDS on the star
 - It then creates an animation by highlighting LED's at a certain coordinate (e.g. x=0)
"""
import math
from time import sleep, time
from gpiozero import LEDBoard

# I've defined four modes of operation: loop over the x-axis, the y-axis, radially or in an angular motion.
MODE = "x"              # can be "x", "y", "x", "radial", "angular"
MAX_BRIGHTNESS = 0.1    # maximum brightness of the LED's (between 0 and 1)
CENTER_MIN_BRIGHTNESS = 0.05 # How much the center circle leds should light up at minimum, which can be pretty
FUZZINESS = 0.01         # Value to indicate how much neighbouring leds should light up (between 0 and 1)
BOOMERANG = True        # Should the animation have a boomerang effect
ANIMATION_SPEED = 0.2   # How fast the animation should run. Recommended is to change this value and keep FPS fixed.
DURATION_IN_SECONDS = 10 # How long should the animation run (use None) to loop indefinitely
ANIMATION_FPS = 30      # Nice framerate


# START OF SCRIPT
# You don't have to change stuff below this point
# Vector manipulation helpers
def add(vec_1, vec_2):
    return [vec_1[0] + vec_2[0], vec_1[1] + vec_2[1]]


def subtract(vec_1, vec_2):
    return [vec_1[0] - vec_2[0], vec_1[1] - vec_2[1]]


def scalar_multiply(scalar, vector):
    return [scalar * i for i in vector]


def polar_to_cartesian(rho, theta):
    return [rho * math.cos(theta), rho * math.sin(theta)]


def cartesian_to_polar(x, y):
    rho = math.sqrt(x ** 2 + y ** 2)
    theta = math.atan2(y, x)
    return [rho, theta]


def to_theta(phi):
    # Polar coordinates work from the x-axis in CCW direction.
    # I'd like to work from the y-axis in CW dir since it's easier in my head
    return math.pi / 2 - phi


def rotate_vector(vector, angle):
    """Rotates vector over an angle
    :param vector: list of 2 numbers
    :param angle: in radians in CW direction
    :return:
    """
    _x = vector[0] * math.cos(angle) + vector[1] * math.sin(angle)
    _y = -vector[0] * math.sin(angle) + vector[1] * math.cos(angle)
    return [_x, _y]


# class used to map pin's on the raspberry to LED's and some basic LED functionality
class Star(LEDBoard):
    # Set up a Star using GPIO Zero to build a class.
    # To use:
    # star = Star() for a simple instance using LED class.
    # star = Star(pwm=True) for a version which can use PWM.
    # See example files in this repo for more examples of use...
    def __init__(self, pwm=False, initial_value=False, pin_factory=None):
        super(Star, self).__init__(
            outer=LEDBoard(
                A=8,B=7,C=12,D=21,E=20,F=16,G=26,H=19,I=13,J=6,K=5,L=11,M=9,
                N=10,O=22,P=27,Q=17,R=4,S=3,T=14,U=23,V=18,W=15,X=24,Y=25,
                pwm=pwm, initial_value=initial_value,
                _order=('A','B','C','D','E','F','G','H','I','J','K','L',
                        'M','N','O','P','Q','R','S','T','U','V','W','X','Y'),
                pin_factory=pin_factory),
            inner=2,
            pwm=pwm, initial_value=initial_value,
            _order=('inner','outer'),
            pin_factory=pin_factory
            )


# class used to store the LED's x,y coordinates and return basic properties
# like the distance from the center, or the angle where angle=0 means the line from the
# center of the star to the first, top LED.
class Led:
    def __init__(self, led, r_center=None):
        self.x = 0
        self.y = 0
        self.led = led
        self.is_center = False
        self.r_center = r_center

    def get_polar(self):
        return (
            cartesian_to_polar(self.x, self.y)
            if not self.is_center
            else [self.r_center, 0]
        )

    def get_cartesian(self):
        return [self.x, self.y]

    def set_polar(self, r, rho):
        self.x = r * math.cos(to_theta(rho))
        self.y = r * math.sin(to_theta(rho))

    def set_cartesian(self, x, y):
        self.x = x
        self.y = y

    def set_led(self, led):
        self.led = led

    def get_led(self):
        return self.led


def calculate_led_positions(star, r_big, r_small, r_center):
    # Position of the first led in polar coordinates
    v_0_p = [r_big, to_theta(0)]
    v_0_xy = polar_to_cartesian(v_0_p[0], v_0_p[1])
    # Position of the first 'indent' of the star in polar coordinates
    v_1_p = [r_small, to_theta(math.pi / 4)]
    v_1_xy = polar_to_cartesian(v_1_p[0], v_1_p[1])

    v_diff_xy = subtract(v_1_xy, v_0_xy)

    # First initialize the leds and omit the center led (it will be added back later)
    leds = [Led(led) for led in star.leds]
    leds[0].set_cartesian(0, 0)
    leds[0].is_center = True
    leds[0].r_center = r_center
    center_led = leds.pop(0)  # Rotate the list so the center led is last

    # calculate the postion of the leds on the outer vertices of the star
    # You only need to calculate 3 led positions. The rest follows from mirror & rotation symmetry
    for led_no in range(3):
        # First calculate the position of the led on the top peak
        # and it's corresponding led on the left, which is mirrored
        #
        # The 3 leds start at the point, and end at 9/10th before the 'inner' point.
        # Therefore, we evenly space them at 3/10th, 6/10th and 9/10th along the vertex
        pos_0 = add(v_0_xy, scalar_multiply(3.0 / 10.0 * led_no, v_diff_xy))
        pos_0_symm = [-pos_0[0], pos_0[1]]

        for point_no in range(5):
            # Position of the led
            led = leds[led_no + point_no * 5]
            led_pos = rotate_vector(pos_0, math.pi * 2 / 5 * point_no)
            led.set_cartesian(led_pos[0], led_pos[1])
            # And the position of the one on the opposite side of the star point
            led_symm = leds[-led_no + point_no * 5]
            led_pos_symm = rotate_vector(pos_0_symm, math.pi * 2 / 5 * point_no)
            led_symm.set_cartesian(led_pos_symm[0], led_pos_symm[1])

    # add back the center led at the end of the array
    leds.append(center_led)
    return leds


def get_brightness(distance, fuzziness):
    if fuzziness == 0:
        corr_factor = 1000
    else:
        corr_factor = 1 / fuzziness
    return round(1 - math.tanh(distance * corr_factor), 2)


def get_brightness_angle(ang1, ang2, led_radius, fuzziness):
    dist = abs(ang1 - ang2)
    dist = dist if dist < math.pi else 2 * math.pi - dist
    dist = math.sin(dist) * led_radius
    return get_brightness(dist, fuzziness)


def animate(
    star,
    leds,
    mode,
    animation_speed,
    animation_fps,
    star_size,
    fuzziness=1,
    seconds=None,
    center_min_value=0,
    boomerang=False,
):
    if mode == "radial":
        min_blink_coordinate = -0.5  # For circles
        max_blink_radius = star_size * 1.3
    elif mode in ["x", "y"]:
        min_blink_coordinate = -star_size * 1.5
        max_blink_radius = star_size * 1.5
    elif mode == "angular":
        min_blink_coordinate = -math.pi  # -R*2
        max_blink_radius = math.pi  # R*2

    # Start the blinking at the  first coordinate
    # This can be anywhere between min_blink_coordinate and max_blink_coordinate
    blink_coordinate = min_blink_coordinate
    try:
        # Set a specified end time when it is given
        t_end = time()
        if seconds is not None:
            t_end += seconds

        while True:
            if seconds is not None and time() > t_end:
                break

            # Just turn BOOMERANG on and you see what it means :)
            if boomerang:
                if blink_coordinate > max_blink_radius:
                    animation_speed = -animation_speed
                if blink_coordinate < min_blink_coordinate:
                    animation_speed = -animation_speed
            else:
                if blink_coordinate > max_blink_radius:
                    blink_coordinate = min_blink_coordinate

            if mode == "radial":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness(abs(led.get_polar()[0] - blink_coordinate)/star_size, fuzziness)
                    for led in leds
                ]
            elif mode == "x":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness(
                        abs(led.get_cartesian()[0] - blink_coordinate)/star_size, fuzziness
                    )
                    for led in leds
                ]
            elif mode == "y":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness(
                        abs(led.get_cartesian()[1] - blink_coordinate)/star_size, fuzziness
                    )
                    for led in leds
                ]
            elif mode == "angular":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness_angle(led.get_polar()[1]/star_size, blink_coordinate, led.get_polar()[0], fuzziness)
                    for led in leds
                ]
                led_filter[-1] = center_min_value
            else:
                raise ValueError(
                    f"Mode '{mode}' not supported. Choose 'x', 'y', 'radial' or 'angular'"
                )

            led_filter[-1] = max(led_filter[-1], center_min_value)

            # This important piece of code actually lights up the leds.
            for idx, led in enumerate(leds):
                led.get_led().value = led_filter[idx]

            sleep(1 / animation_fps)
            blink_coordinate += animation_speed
    except KeyboardInterrupt:
        star.close()


if __name__ == "__main__":
    # This is the main flow of the application

    # The flow start with initializing the raspberry pins to the leds here:
    STAR = Star(pwm=True)

    # Set the radius of the star shape's outer and inner circle. For more info,
    # check https://miro.medium.com/max/1400/1*2j6CODCoHR4YGAd_KovL9w.png
    R_BIG = 1  # Normalized size of the star
    if MODE == "radial":
        # For radial animations, having a small R_SMALL is prettier
        # It makes the leds on the star edge seem closer to the center LED's.
        R_SMALL = R_BIG / 5
    else:
        # This is more realistic considering the size of the actual star
        R_SMALL = R_BIG * 3.5 / 5

    # Set the perceived radius of the center led circle for radial animations. Useful for timing.
    # This sets it to slightly smaller than the distance towards the 'indent' of the star-shape
    R_CENTER = (
        R_SMALL - (R_BIG - R_SMALL) / 10
    )

    # Calculate the x,y coordinates of the led's on the star
    leds_list = calculate_led_positions(STAR, R_BIG, R_SMALL, R_CENTER)
    animate(
        star=STAR,
        leds=leds_list,
        mode=MODE,
        animation_speed=ANIMATION_SPEED,
        animation_fps=ANIMATION_FPS,
        star_size=R_BIG,
        fuzziness=FUZZINESS,
        seconds=DURATION_IN_SECONDS,
        center_min_value=CENTER_MIN_BRIGHTNESS,
        boomerang=BOOMERANG,
    )

    STAR.off()
