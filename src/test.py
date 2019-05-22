import random

from captchacha.image import captcha
from captchacha.image import text, background, offset, rotate
from captchacha.image import curve, noise, smooth


if __name__ == '__main__':
    import string
    import os

    color_choices = ('#674331', '#515329', '#725a38', '#68483e', '#7b2616', '#53595f')

    def random_color():
        return random.choice(color_choices)

    current_path = os.path.split(os.path.realpath(__file__))[0]
    captcha_image = captcha(drawings=[
        background('#a5a4aa'),  # #a5a4aa #aeada8
        text(fonts=[os.path.join(current_path, '../fonts/CourierNew-Bold.ttf'),
                    os.path.join(current_path, '../fonts/Arial-Bold.ttf'),
                    os.path.join(current_path, '../fonts/CourierNew.ttf'),
                    os.path.join(current_path, '../fonts/Arial.ttf')],
             color=random_color,
             drawings=[
                 # warp(),
                 rotate(angle=45),
                 offset()
             ], squeeze_factor=0.6),
        curve(),
        noise(),
        smooth()
    ], width=203, height=66)
    image = captcha_image(random.sample(string.ascii_uppercase + string.digits, 6))
    image.save('sample.jpg', 'JPEG', quality=75)
