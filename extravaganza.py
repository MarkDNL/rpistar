import math
import numpy as NP
from star import Star
from time import sleep, time

MAX_BRIGHTNESS = 0.3

# START OF SCRIPT
# You don't have to change stuff below this point

def polar_to_cartesian(rho, theta):
    return [rho * math.cos(theta), rho * math.sin(theta)]

def cartesian_to_polar(x, y):
    rho = NP.sqrt(x ** 2 + y ** 2)
    theta = NP.arctan2(y, x)
    return [rho, theta]

# Polar coordinates work from the x-axis in CCW direction.
# I'd like to work from the y-axis in CW dir since it's easier in my head
def to_theta(phi):
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
    v_diff_xy = NP.subtract(v_1_xy, v_0_xy)

    leds = [Led(led) for led in star.leds]
    leds[0].set_cartesian(0, 0)
    leds[0].is_center = True
    leds[0].r_center = r_center
    center_led = leds.pop(0)  # Rotate the list so the center led is last

    # You only need to calculate 3 positions, the rest follows from mirror & rotation symmetry
    for led_no in range(3):
        # First calculate the position of the led on the top peak
        # and it's corresponding led on the left, which is mirrored
        #
        # The 3 leds start at the point, and end at 9/10th before the 'inner' point.
        # Therefore, we evenly space them at 3/10th, 6/10th and 9/10th along the vertex
        pos_0 = NP.add(v_0_xy, 3 / 10 * led_no * v_diff_xy)
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

    leds.append(center_led)
    return leds

def get_brightness(distance, fuzziness):
    if fuzziness == 0:
        corr_factor = 1000
    else:
        corr_factor = 1 / fuzziness
    return round(1 - math.tanh(distance * corr_factor), 2)

def get_brightness_angle(ang1, ang2, fuzziness):
    if fuzziness == 0:
        corr_factor = 3 * 1000
    else:
        corr_factor = 3 * 1 / fuzziness

    dist = abs(ang1 - ang2)
    dist = dist if dist < math.pi else 2 * math.pi - dist
    return round(1 - math.tanh(dist * corr_factor), 2)
    def animate(
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
        min_blink_radius = -0.5  # For circles
        max_blink_radius = star_size * 1.3
    elif mode in ["x", "y"]:
        min_blink_radius = -star_size * 1.5
        max_blink_radius = star_size * 1.5
    elif mode == "angular":
        min_blink_radius = -math.pi  # -R*2
        max_blink_radius = math.pi  # R*2
    blink_radius = min_blink_radius
    try:
        t_end = time()
        if seconds is not None:
            t_end += seconds
        while True:
            if seconds is not None and time() > t_end:
                break

            if boomerang:
                if blink_radius > max_blink_radius:
                    animation_speed = -animation_speed
                if blink_radius < min_blink_radius:
                    animation_speed = -animation_speed
            else:
                if blink_radius > max_blink_radius:
                    blink_radius = min_blink_radius

            if mode == "radial":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness(abs(led.get_polar()[0] - blink_radius), fuzziness)
                    for led in leds
                ]
            elif mode == "x":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness(
                        abs(led.get_cartesian()[0] - blink_radius), fuzziness
                    )
                    for led in leds
                ]
            elif mode == "y":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness(
                        abs(led.get_cartesian()[1] - blink_radius), fuzziness
                    )

                ]
            elif mode == "angular":
                led_filter = [
                    MAX_BRIGHTNESS
                    * get_brightness_angle(led.get_polar()[1], blink_radius, fuzziness)
                    for led in leds
                ]
                led_filter[-1] = center_min_value
            else:
                raise ValueError(
                    f"Mode '{mode}' not supported. Choose 'x', 'y', 'radial' or 'angular'"
                )

            led_filter[-1] = max(led_filter[-1], center_min_value)
            for idx, led in enumerate(leds):
                led.get_led().value = led_filter[idx]
            sleep(1 / animation_fps)
            blink_radius += animation_speed
    except KeyboardInterrupt:
        star.close()

if __name__ == "__main__":
    star = Star(pwm=True)
    R_BIG = 5  # Radius of the star towards the outer points (e.g. 5 cm)
    seconds = [6, 7, 3, 4, 12]
    for idx, mode in enumerate(["x", "y", "x", "radial", "angular"]):
        if mode == "radial":
            # r=2.5 if it needs to be realistic. For radial animations, r=1 is prettier.
            R_SMALL = 1
        else:
            R_SMALL = 4
        R_CENTER = (
            R_SMALL - (R_BIG - R_SMALL) / 10
        )  # Perceived radius of the center led circle for radial animations
        FUZZINESS = 0.7
        BOOMERANG = False
        ANIMATION_SPEED = 0.6
        CENTER_MIN_VALUE = 0.05
        ANIMATION_FPS = 30

        leds_list = calculate_led_positions(star, R_BIG, R_SMALL, R_CENTER)
        animate(
            leds_list,
            mode,
            ANIMATION_SPEED,
            ANIMATION_FPS,
            R_BIG,
            fuzziness=FUZZINESS,
            seconds=seconds[idx],
            center_min_value=CENTER_MIN_VALUE,
            boomerang=BOOMERANG,
        )
        if mode == 'x' and idx == 2:
            star.off()
            sleep(1)
    star.off()