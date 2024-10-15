from zpl.elements import TextElement, BarcodeElement, LogoElement, LineElement, BoxElement, ImageElement
from zpl.label import Label
import os
from PIL import Image
import traceback

print("Script started")

def parse_zpl(zpl_data):
    label = Label(800, 1200)  # Adjust size as needed
    state = {
        'current_x': 0,
        'current_y': 0,
        'current_font_size': 12,
        'barcode_type': None,
        'barcode_data': None,
        'barcode_width': None,
        'barcode_height': None,
        'reverse_field': False,  
        'current_font_bold': False,
        'current_barcode_type': 'code128',
        'current_barcode_height': 10,
        'current_barcode_width': 1,
        'field_data': ''  # Initialize field_data
    }

    def handle_fo(parts):
        if len(parts) == 2:
            state['current_x'], state['current_y'] = map(int, parts)
            print(f"Set position to ({state['current_x']}, {state['current_y']})")

    def handle_gb(parts):
        print("GB command received")
        print(f"Received parts: {parts}")
        print(f"Current reverse_field state: {state['reverse_field']}")
        
        if len(parts) >= 3:
            width, height, thickness = map(int, parts[:3])
            color = 'B'  # Default color is Black
            if len(parts) >= 4:
                color = parts[3].upper()  # Get the color parameter if provided
            rounding = 0  # Default rounding
            if len(parts) >= 5:
                rounding = int(parts[4])  # Get the rounding parameter if provided
            
            print(f"GB command: width={width}, height={height}, thickness={thickness}, color={color}, rounding={rounding}")
            
            # Convert color to RGB
            rgb_color = (0, 0, 0) if color == 'B' else (255, 255, 255)
            
            # Ensure height is at least 1 pixel
            height = max(height, 1)
            
            element = BoxElement(
                state['current_x'],
                state['current_y'],
                width,
                height,
                thickness,
                line_color=rgb_color,
                fill_color=rgb_color if thickness == 0 else None,
                reverse=state['reverse_field']
            )
            label.add_element(element)
            print(f"Added element: {element}")
            
            # Turn off reverse field after use
            state['reverse_field'] = False
            print("Reverse field turned off after element creation")
        else:
            print(f"Insufficient parameters for GB command. Expected at least 3, got {len(parts)}")

    def handle_by(parts):
        if parts and parts[0] == '7':
            state['current_barcode_type'] = 'gs1-128'
            print("Set barcode type to GS1-128")
        else:
            state['current_barcode_type'] = 'code128'
            print("Set barcode type to Code 128")

    def handle_bc(parts):
        print(f"Handling BC command with parts: {parts}")
        if parts:
            orientation = parts[0] if parts[0] in ['N', 'R', 'I', 'B'] else 'N'
            height = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            line = parts[2] if len(parts) > 2 and parts[2] in ['Y', 'N'] else 'Y'
            lineAbove = parts[3] if len(parts) > 3 and parts[3] in ['Y', 'N'] else 'N'
            checkDigit = parts[4] if len(parts) > 4 and parts[4] in ['Y', 'N'] else 'N'
            mode = parts[5] if len(parts) > 5 and parts[5] in ['N', 'U', 'A', 'D'] else 'N'

            print(f"BC command: orientation={orientation}, height={height}, line={line}, "
                  f"lineAbove={lineAbove}, checkDigit={checkDigit}, mode={mode}")

            state['pending_barcode'] = {
                'type': 'code128',
                'orientation': orientation,
                'height': height,
                'line': line,
                'lineAbove': lineAbove,
                'checkDigit': checkDigit,
                'mode': mode,
                'total_width': 700  # Default width, adjust as needed
            }
            print(f"Barcode parameters set, waiting for data.")
        else:
            print("Insufficient parameters for BC command")

    def handle_fd(parts):
        print(f"Handling FD command with text: {parts[0] if parts else ''}")
        if parts:
            state['field_data'] = parts[0]
            if 'pending_barcode' in state:
                # This is barcode data
                barcode_element = BarcodeElement(
                    state['current_x'],
                    state['current_y'],
                    state['field_data'],
                    width=state['pending_barcode'].get('total_width', 100),  # Use get() with default
                    height=state['pending_barcode']['height'],
                    barcode_type=state['pending_barcode']['type']
                )
                label.add_element(barcode_element)
                print(f"Added barcode element: {barcode_element}")
                del state['pending_barcode']
            else:
                # This is regular text data
                text_element = TextElement(
                    state['current_x'],
                    state['current_y'],
                    state['field_data'],
                    font_size=state.get('current_font_size', 12),
                    bold=state.get('current_font_bold', False),
                    reverse=state.get('reverse_field', False)
                )
                label.add_element(text_element)
                print(f"Added text element: {text_element}")
        else:
            print("No field data provided for FD command")

    def handle_cf(parts):
        if len(parts) >= 2:
            state['current_font_size'] = int(parts[1])
            print(f"Changed font size to {state['current_font_size']}")

    def handle_gf(parts):
        print(f"Handling GF command")
        print(f"Number of parts: {len(parts)}")
        if len(parts) >= 5:
            format, total, total_bytes, bytes_per_row, *data_parts = parts
            
            print(f"GF command parts:")
            print(f"  format: {format}")
            print(f"  total: {total}")
            print(f"  total_bytes: {total_bytes}")
            print(f"  bytes_per_row: {bytes_per_row}")
            print(f"  data_parts length: {len(data_parts)}")
            
            full_data = ','.join(data_parts)  # Use ''.join instead of ','.join
            
            # Calculate image dimensions
            bytes_per_row = int(bytes_per_row)
            width = bytes_per_row * 8
            height = int(total) // bytes_per_row

            print(f"Calculated dimensions: {width}x{height}")
            
            image_element = ImageElement(
                state['current_x'],
                state['current_y'],
                width,
                height,
                full_data,
                format
            )
            label.add_element(image_element)
            print(f"Adding image at position ({state['current_x']}, {state['current_y']}) with size {width}x{height}")
        else:
            print("Insufficient parameters for GF command")
            print(f"Received parts: {parts}")

    def handle_fs(parts):
        print("FS command received - Field Separator")
        state['reverse_field'] = False  # Reset reverse field after each field

    def handle_fr(parts):
        print("FR command received - Reverse Field mode activated")
        state['reverse_field'] = True

    def handle_a0(parts):
        if len(parts) >= 3:
            font_name, font_width, font_height = parts[:3]
            
            # Determine if the font should be bold
            is_bold = font_name in ['0', '2', '4', '6', '8']
            
            # Set font size (you may need to adjust this calculation)
            font_size = max(int(font_height), 12)  # Ensure minimum font size of 12
            
            state['current_font_size'] = font_size
            state['current_font_bold'] = is_bold
            
            print(f"Font set: size={font_size}, bold={is_bold}")
        else:
            print("Insufficient parameters for A0 command")

    def handle_pw(parts):
        if parts:
            width = parts[0].strip()  # Remove leading/trailing whitespace and newlines
            try:
                width = int(width)
                print(f"Setting label width to: {width}")
                state['label_width'] = width
            except ValueError:
                print(f"Invalid width value for PW command: {width}")
        else:
            print("Insufficient parameters for PW command")

    def handle_ci(parts):
        if parts:
            code_page = parts[0]
            print(f"Setting code page to: {code_page}")
            # You might need to implement code page handling if necessary
        else:
            print("Insufficient parameters for CI command")

    def handle_bx(parts):
        state['current_barcode_type'] = 'datamatrix'
        print("Set barcode type to DataMatrix")
        
        # Default values
        orientation = 'N'
        height = 50
        quality = 200
        columns = 10
        rows = 10
        format = 6
        escape = 'FNC1'
        ratio = 1
        
        # Parse parameters
        if len(parts) > 0:
            orientation = parts[0] or orientation
        if len(parts) > 1:
            height = int(parts[1]) if parts[1] else height
        if len(parts) > 2:
            quality = int(parts[2]) if parts[2] else quality
        if len(parts) > 3:
            columns = int(parts[3]) if parts[3] else columns
        if len(parts) > 4:
            rows = int(parts[4]) if parts[4] else rows
        if len(parts) > 5:
            format = int(parts[5]) if parts[5] else format
        if len(parts) > 6:
            escape = parts[6] or escape
        if len(parts) > 7:
            ratio = int(parts[7]) if parts[7] else ratio
        
        # Store parameters in state
        state['datamatrix'] = {
            'orientation': orientation,
            'height': height,
            'quality': quality,
            'columns': columns,
            'rows': rows,
            'format': format,
            'escape': escape,
            'ratio': ratio
        }
        
        print(f"DataMatrix configuration: orientation={orientation}, height={height}, quality={quality}, "
              f"columns={columns}, rows={rows}, format={format}, escape={escape}, ratio={ratio}")

    command_handlers = {
        'FO': handle_fo,  # Field Origin - Sets the position for subsequent fields
        'GB': handle_gb,  # Graphic Box - Draws lines or boxes
        'BY': handle_by,  # Bar Code Field Default - Sets default barcode parameters
        'BC': handle_bc,  # Bar Code - Specifies a barcode type (e.g., Code 128)
        'FD': handle_fd,  # Field Data - Specifies the data for text or barcode fields
        'CF': handle_cf,  # Change Alphanumeric Font - Changes the font or font size
        'GF': handle_gf,
        'FS': handle_fs,  # Graphic Field - Adds an image or logo to the label
        'FR': handle_fr,
        'A0': handle_a0,
        'PW': handle_pw,
        'CI': handle_ci,
        'BX': handle_bx   # DataMatrix 
    }

    commands = zpl_data.strip().split('^')
    for command in commands:
        if not command:
            continue
        if command.startswith('XZ'):
            break  # End of ZPL data
        cmd = command[:2]
        parts = command[2:].split(',')
        
        if cmd in command_handlers:
            command_handlers[cmd](parts)
        else:
            print(f"Unknown or unhandled command: {cmd}")

    return label

def read_zpl_data(filename):
    with open(filename, 'r') as file:
        return file.read()

def main():
    try:
        print("Script started")
        print("Entering main function")
        
        filename = "zpl_data.txt"
        print(f"Reading ZPL data from file: {filename}")
        
        zpl_data = read_zpl_data(filename)
        print("ZPL data read successfully:", zpl_data[:100] + "...")
        
        print("Parsing ZPL data")
        label = parse_zpl(zpl_data)
        
        # After processing all commands and drawing elements
        output_directory = os.path.expanduser('~/.cursor-tutor')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        output_file = os.path.join(output_directory, 'output.png')
        
        # Assuming 'label' is your Label object
        image = label.render()
        image.save(output_file)
        print(f"Label saved successfully as: {output_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()

    print("Script finished")

if __name__ == "__main__":
    main()

    
