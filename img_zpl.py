import math
from PIL import Image

# Mapping values
map_code = {
    1: "G", 2: "H", 3: "I", 4: "J", 5: "K", 6: "L", 7: "M", 8: "N", 9: "O", 10: "P", 11: "Q", 12: "R", 13: "S", 14: "T", 15: "U",
    16: "V", 17: "W", 18: "X", 19: "Y", 20: "g", 40: "h", 60: "i", 80: "j", 100: "k", 120: "l", 140: "m", 160: "n", 180: "o", 200: "p",
    220: "q", 240: "r", 260: "s", 280: "t", 300: "u", 320: "v", 340: "w", 360: "x", 380: "y", 400: "z"
}

class IMG_ZPL:
    def __init__(self):
        self.black_limit = 380
        self.total = 0
        self.width_bytes = 0
        self.compress_hex = False

    def convert_from_image(self, image_path):
        # Open the image, ensuring compatibility with PNG, JPG, and BMP formats
        image = Image.open(image_path).convert("RGB")
        hex_ascii = self.create_body(image)
        if self.compress_hex:
            hex_ascii = self.encode_hex_ascii(hex_ascii)

        zpl_code = "^GFA,{},{},{},{}".format(self.total, self.total, self.width_bytes, hex_ascii)


        return zpl_code

    def create_body(self, bitmap_image):
        sb = []
        width, height = bitmap_image.size
        index = 0
        aux_binary_char = ['0', '0', '0', '0', '0', '0', '0', '0']
        self.width_bytes = math.ceil(width / 8)
        self.total = self.width_bytes * height

        for h in range(height):
            for w in range(width):
                rgb = bitmap_image.getpixel((w, h))  # Returns a tuple (R, G, B)
                red, green, blue = rgb  # Unpack the tuple directly
                
                aux_char = '1'
                total_color = red + green + blue
                if total_color > self.black_limit:
                    aux_char = '0'
                
                aux_binary_char[index] = aux_char
                index += 1
                if index == 8 or w == (width - 1):
                    sb.append(self.four_byte_binary(''.join(aux_binary_char)))
                    aux_binary_char = ['0', '0', '0', '0', '0', '0', '0', '0']
                    index = 0
            sb.append("\n")
        
        return ''.join(sb)

    def four_byte_binary(self, binary_str):
        decimal = int(binary_str, 2)
        if decimal > 15:
            return hex(decimal)[2:].upper()
        else:
            return "0" + hex(decimal)[2:].upper()

    def encode_hex_ascii(self, code):
        max_line = self.width_bytes * 2
        sb_code = []
        sb_line = []
        previous_line = None
        counter = 1
        first_char = False
        aux = code[0]
        
        for i in range(1, len(code)):
            if first_char:
                aux = code[i]
                first_char = False
                continue
            if code[i] == '\n':
                if counter >= max_line and aux == '0':
                    sb_line.append(",")
                elif counter >= max_line and aux == 'F':
                    sb_line.append("!")
                elif counter > 20:
                    multi_20 = (counter // 20) * 20
                    resto_20 = (counter % 20)
                    sb_line.append(map_code.get(multi_20))
                    if resto_20 != 0:
                        sb_line.append(map_code.get(resto_20) + aux)
                    else:
                        sb_line.append(aux)
                else:
                    sb_line.append(map_code.get(counter) + aux)
                counter = 1
                first_char = True
                if ''.join(sb_line) == previous_line:
                    sb_code.append(":")
                else:
                    sb_code.append(''.join(sb_line))
                previous_line = ''.join(sb_line)
                sb_line.clear()
                continue
            if aux == code[i]:
                counter += 1
            else:
                if counter > 20:
                    multi_20 = (counter // 20) * 20
                    resto_20 = (counter % 20)
                    sb_line.append(map_code.get(multi_20))
                    if resto_20 != 0:
                        sb_line.append(map_code.get(resto_20) + aux)
                    else:
                        sb_line.append(aux)
                else:
                    sb_line.append(map_code.get(counter) + aux)
                counter = 1
                aux = code[i]
        
        return ''.join(sb_code)

    def set_compress_hex(self, compress_hex):
        self.compress_hex = compress_hex

    def set_blackness_limit_percentage(self, percentage):
        self.black_limit = (percentage * 768 // 100)



if __name__=="__main__":
    zpl_converter = IMG_ZPL()
    zpl_converter.set_compress_hex(True)  # Set compress hex if needed
    zpl_converter.set_blackness_limit_percentage(99)  # Set blackness limit (percentage)

    image_path = 'logo.png'  # Update with your image path
    zpl_code = zpl_converter.convert_from_image(image_path)
    print(zpl_code)