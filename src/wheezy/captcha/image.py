"""
"""

import random
from typing import Union, Callable

from wheezy.captcha.comp import Draw
from wheezy.captcha.comp import Image
from wheezy.captcha.comp import ImageFilter
from wheezy.captcha.comp import getrgb
from wheezy.captcha.comp import truetype
from wheezy.captcha.comp import xrange


def captcha(drawings, width=200, height=75):
    def render(text_):
        image_ = Image.new('RGB', (width, height), (255, 255, 255))
        for drawing in drawings:
            image_ = drawing(image_, text_)
            assert image_
        return image_
    return render


# ------------------------------ region: captcha drawers ------------------------------ #

def background(color='#EEEECC'):
    """ 验证码底色

    必须第一个调用，因为底色上色方法是画了一个矩形
    """
    color = getrgb(color)

    def drawer(image_, text_):
        Draw(image_).rectangle([(0, 0), image_.size], fill=color)
        return image_
    return drawer


def smooth():
    """验证码进行模糊"""
    def drawer(image_, text_):
        return image_.filter(ImageFilter.SMOOTH)
    return drawer


def curve(color='#5C87B2', width=4, number=6):
    """验证码添加干扰线"""
    from wheezy.captcha.bezier import make_bezier
    if not callable(color):
        c = getrgb(color)

        def color():
            return c

    def drawer(image_, text_):
        dx, height = image_.size
        dx = dx / number
        path = [(dx * i, random.randint(0, height))
                for i in range(1, number)]
        bcoefs = make_bezier(number - 1)
        points = []
        for coefs in bcoefs:
            points.append(tuple(sum([coef * p for coef, p in zip(coefs, ps)])
                          for ps in zip(*path)))
        draw = Draw(image_)
        draw.line(points, fill=color(), width=width)
        return image_
    return drawer


def noise(number=50, color='#EEEECC', level=2):
    """验证码填充随机噪声点"""
    if not callable(color):
        c = getrgb(color)

        def color():
            return c

    def drawer(image_, text_):
        width, height = image_.size
        dx = width / 10
        width = width - dx
        dy = height / 10
        height = height - dy
        draw = Draw(image_)
        for i in xrange(number):
            x = int(random.uniform(dx, width))
            y = int(random.uniform(dy, height))
            draw.line(((x, y), (x + level, y)), fill=color(), width=level)
        return image_
    return drawer


def text(fonts, font_sizes=None, drawings=None, color: Union[str, Callable] = '#5C87B2', squeeze_factor=0.8):
    """ 向验证码上写文字

    :param fonts: ttf 字体文件，Iterable
    :param font_sizes: 字体大小，Iterable

    真正的字体是 fonts 和 font_sizes 的笛卡尔积

    :param drawings: 文字变换(混淆)方法，每生成一个字母，所有 drawings 都会变换这个字母
    :param color: 文字颜色，或者是一个返回颜色的函数 (例如随机颜色)
    :param squeeze_factor: 挤压的比例，这个值越低，验证码重叠程度越高
    """

    fonts = tuple(truetype(name, size)
                  for name in fonts
                  for size in font_sizes or (65, 70, 75))
    if not callable(color):
        c = getrgb(color)

        def color():
            return c

    def drawer(image_, text_):
        draw = Draw(image_)
        char_images = []
        for c_ in text_:
            font = random.choice(fonts)
            c_width, c_height = draw.textsize(c_, font=font)
            # char_image = Image.new('RGB', (c_width, c_height), (0, 0, 0))
            o_width, o_height = font.getoffset(c_)
            char_image = Image.new(mode='RGB', size=(c_width + o_width, c_height + o_height), color=(0, 0, 0))
            char_draw = Draw(char_image)
            char_draw.text((0, 0), c_, font=font, fill=color())
            char_image = char_image.crop(char_image.getbbox())
            for drawing in drawings:
                char_image = drawing(char_image)
            char_images.append(char_image)
        width, height = image_.size
        offset_ = int(
            (
                width -
                sum(int(i.size[0] * squeeze_factor) for i in char_images[:-1]) -
                char_images[-1].size[0]
            ) / 2
        )
        # 将单个字符图像画在验证码上
        for char_image in char_images:
            c_width, c_height = char_image.size
            mask = char_image.convert('L').point(lambda i: i * 1.97)
            image_.paste(char_image,
                         (offset_, int((height - c_height) / 2)),
                         mask)
            offset_ += int(c_width * squeeze_factor)
        return image_

    return drawer


# ------------------------------ region: text drawers ------------------------------ #

def warp(dx_factor=0.27, dy_factor=0.21):
    """单个字符变形
    随机改变图片四个角的坐标，并进行先行变换
    """

    def drawer(image_):
        width, height = image_.size
        dx = width * dx_factor
        dy = height * dy_factor
        x1 = int(random.uniform(-dx, dx))
        y1 = int(random.uniform(-dy, dy))
        x2 = int(random.uniform(-dx, dx))
        y2 = int(random.uniform(-dy, dy))
        image2 = Image.new('RGB',
                           (width + abs(x1) + abs(x2),
                            height + abs(y1) + abs(y2)))
        image2.paste(image_, (abs(x1), abs(y1)))
        width2, height2 = image2.size
        return image2.transform(
            (width, height), Image.QUAD,
            (x1, y1,
             -x1, height2 - y2,
             width2 + x2, height2 + y2,
             width2 - x2, -y1))
    return drawer


def offset(dx_factor=0.1, dy_factor=0.2):
    """单个字符随机位置移动"""
    def drawer(image_):
        width, height = image_.size
        dx = int(random.random() * width * dx_factor)
        dy = int(random.random() * height * dy_factor)
        image2 = Image.new('RGB', (width + dx, height + dy))
        image2.paste(image_, (dx, dy))
        return image2
    return drawer


def rotate(angle=25):
    """单个字符旋转
    正负 angle 角度之间随机旋转
    """
    def drawer(image_):
        return image_.rotate(
            random.uniform(-angle, angle), Image.BILINEAR, expand=1)
    return drawer


if __name__ == '__main__':
    import string
    import os

    color_choices = ('#674331', '#515329', '#725a38', '#68483e', '#7b2616', '#53595f')

    def random_color():
        return random.choice(color_choices)

    current_path = os.path.split(os.path.realpath(__file__))[0]
    captcha_image = captcha(drawings=[
        background('#a5a4aa'),  # #a5a4aa #aeada8
        text(fonts=[os.path.join(current_path, '../../../fonts/CourierNew-Bold.ttf'),
                    os.path.join(current_path, '../../../fonts/Arial-Bold.ttf'),
                    os.path.join(current_path, '../../../fonts/CourierNew.ttf'),
                    os.path.join(current_path, '../../../fonts/Arial.ttf')],
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
