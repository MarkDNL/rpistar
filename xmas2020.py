from star import Star
from time import sleep
from datetime import timezone, datetime, timedelta
import pytz
import math
NL_TZ = pytz.timezone('Europe/Amsterdam')
star = Star(pwm=True)
DAY_START_HOUR = 4  # partying until 4AM is allowed. After that, it's embarrassing. Go to bed.
BEER_HOUR = 16
ON_BRIGHTNESS = 0.1
try:
    leds = list(star.leds)
    # Rotate the list so the center of the star comes last
    leds.append(leds.pop(0))
    while True:
        # Timezones suck
        now = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(NL_TZ)
        if DAY_START_HOUR >= now.hour or now.hour >= BEER_HOUR:
            # It's beer time!
            pulse_index = 25
            led_filter = [ON_BRIGHTNESS] * 26
        else:
            # No beer yet :(
            # Count hours until it's time
            led_filter = [0] * 26
            next_beer_time = NL_TZ.localize(datetime(now.year, now.month, now.day, BEER_HOUR)).astimezone(NL_TZ)
            duration_in_seconds = (next_beer_time - now).seconds
            max_duration = BEER_HOUR * 3600.0
            pulse_index = int(25 - math.floor(duration_in_seconds / max_duration * 25.0))
            led_filter[0:pulse_index] = [ON_BRIGHTNESS] * (pulse_index + 1)
        for idx, led in enumerate(leds):
            led.value = led_filter[idx]
            if idx == pulse_index:
                led.pulse()
            sleep(0.25)
        sleep(60)
        star.off()
        sleep(2)
except KeyboardInterrupt:
    star.close()
