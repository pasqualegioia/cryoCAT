import numpy as np

from cryocat.ioutils import *
import tempfile
import pytest
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# function to create a temporary file with a specific encoding
def create_temp_file_with_encoding(content, encoding):
    """Creates a temporary file with the specified encoding."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding=encoding)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

#not working yet: iso88591 and windows1252 are very similar?
@pytest.mark.parametrize("content, encoding, expected_encoding", [
    ("hello, this is a test.", "utf-8", "utf-8"),
    ("hello, this is a test with é.", "iso-8859-1", "iso-8859-1"),  # Added accented character for testing
    ("hello, this is a test with € symbol.", "windows-1252", "windows-1252"),  # Euro symbol for testing
])
def test_get_file_encoding_valid(content, encoding, expected_encoding):
    """Test the get_file_encoding function for various encodings."""
    # Create the temporary file with the specified encoding
    temp_file_path = create_temp_file_with_encoding(content, encoding)

    # Verify that the file's content matches what was written
    with open(temp_file_path, 'r', encoding=encoding) as f:
        file_content = f.read()
        assert file_content == content  # Make sure the content is as expected

    # Check if get_file_encoding detects the encoding correctly
    detected_encoding = get_file_encoding(temp_file_path)
    print(f"Detected encoding: {detected_encoding}")

    # Validate the detected encoding matches the expected encoding
    assert detected_encoding == expected_encoding

    # Clean up the temporary file after the test
    os.remove(temp_file_path)

#modified is_flat function, throw exceptions
def test_is_float():
    # valid float inputs
    assert is_float(3.14) == True
    assert is_float(0.0) == True
    assert is_float(-5.67) == True
    assert is_float("3.14") == True
    # not valid inputs
    assert is_float("hello") == False
    assert is_float(None) == False  # None value
    assert is_float("123abc") == False
    assert is_float([]) == False  #raise exception
    assert is_float({}) == False
    assert is_float(True) == False
    assert is_float(False) == False

#case to handle: input is None, create exception class?
def test_get_filename_from_path():
    #filename with extension
    input_path = "/home/user/documents/file.txt"
    expected = "file.txt"
    assert get_filename_from_path(input_path) == expected
    #filename without extension
    input_path = "/home/user/documents/file.txt"
    expected = "file"
    assert get_filename_from_path(input_path, with_extension=False) == expected
    #filename with no extension
    input_path = "file"
    expected = "file"
    assert get_filename_from_path(input_path) == expected
    #multiple directories
    input_path = "/home/user/documents/folder/subfolder/file.txt"
    expected = "file.txt"
    assert get_filename_from_path(input_path) == expected
    #multiple directories without extension
    input_path = "/home/user/documents/folder/subfolder/file.txt"
    expected = "file"
    assert get_filename_from_path(input_path, with_extension=False) == expected
    #with a file that has no extension
    input_path = "/home/user/documents/folder/subfolder/no_extension"
    expected = "no_extension"
    assert get_filename_from_path(input_path) == expected
    #containing a dot but no extension
    input_path = "/home/user/documents/file.withoutextension"
    expected = "file.withoutextension"
    assert get_filename_from_path(input_path) == expected
    #empty path
    input_path = ""
    expected = ""
    assert get_filename_from_path(input_path) == expected

    #leading/trailing spaces
    input_path = "  /home/user/documents/file.txt  "
    expected = "file.txt"
    assert get_filename_from_path(input_path.strip()) == expected

    #special characters in the filename
    input_path = "/home/user/documents/special@file#name!.txt"
    expected = "special@file#name!.txt"
    assert get_filename_from_path(input_path) == expected
    #unicode characters
    input_path = "/home/user/documents/file_éxample.txt"
    expected = "file_éxample.txt"
    assert get_filename_from_path(input_path) == expected
    #long file path
    input_path = "/home/user/documents/" + "a" * 255 + ".txt"
    expected = "a" * 255 + ".txt"
    assert get_filename_from_path(input_path) == expected

    #multiple dots but no extension
    input_path = "/home/user/documents/file.with.many.dots"
    expected = "file.with.many.dots"
    assert get_filename_from_path(input_path) == expected

    #TO ADD EXCEPTION, to check this edge case
    #not a string
    """
    input_path = None
    expected = None
    assert get_filename_from_path(input_path) == expected
    """

    #edge case
    input_path = "/home/user/documents/.hiddenfile.txt"
    expected = ".hiddenfile.txt"
    assert get_filename_from_path(input_path) == expected
    #containing only dots
    input_path = "/home/user/documents/...."
    expected = "...."
    assert get_filename_from_path(input_path) == expected

    #spaces in filename
    input_path = "/home/user/documents/file with spaces.txt"
    expected = "file with spaces.txt"
    assert get_filename_from_path(input_path) == expected

#some cases to think about
def test_get_number_of_lines_with_character():
    # create a temporary file for testing
    test_filename = "test_file.txt"

    # write test data to the file
    with open(test_filename, "w") as file:
        file.write("# this is a comment line\n")  # starts with '#'
        file.write("this is a normal line\n")  # does not start with '#'
        file.write("# another comment line\n")  # starts with '#'
        file.write("\n")  # empty line
        file.write("# yet another comment\n")  # starts with '#'
        file.write("last normal line\n")  # does not start with '#'
        file.write("some text with # in middle\n")  # '#' in middle, not at start

        #Space before the character
        #file.write(" # a line with leading space\n")  # '#' after leading space
        #Spaces before the character
        #file.write("  #\n")  # '#' after multiple spaces

        file.write("#\n")  # line with only '#'



    # test lines starting with the '#' character
    character = "#"
    expected = 4  # six lines start directly with '#'
    assert get_number_of_lines_with_character(test_filename, character) == expected


    # clean up temporary file
    os.remove(test_filename)

def test_fileformat_replace_pattern():
    #padding needed
    assert fileformat_replace_pattern("some_text_$AAA_rest", 79, "A") == "some_text_079_rest"
    #no padding needed
    assert fileformat_replace_pattern("file_/$AAA/$B.txt", 123, "A") == "file_/123/$B.txt"
    #number too big for pattern
    with pytest.raises(ValueError, match=re.escape("Number '12345' has more digits than string '$A'.")):
        fileformat_replace_pattern("file_/$A/$B.txt", 12345, "A")
    #pattern not present -raise exception
    with pytest.raises(ValueError, match=re.escape("The format file_/$A/$B.txt does not contain any sequence of \\$ followed by C.")):
        fileformat_replace_pattern("file_/$A/$B.txt", 123, "C")
    #no error if pattern is absent and raise_error false
    assert fileformat_replace_pattern("file_/$A/$B.txt", 123, "C", raise_error=False) == "file_/$A/$B.txt"
    #other multiple cases
    assert fileformat_replace_pattern("file_$AA_$BB_end", 7, "A") == "file_07_$BB_end"
    assert fileformat_replace_pattern("file_$AA_$BB_end", 5, "B") == "file_$AA_05_end"
    #complex input and multiple patterns
    assert fileformat_replace_pattern("path_$AAA/$BB/$CC_$DD.txt", 42, "A") == "path_042/$BB/$CC_$DD.txt"
    assert fileformat_replace_pattern("path_$AAA/$BB/$CC_$DD.txt", 3, "B") == "path_$AAA/03/$CC_$DD.txt"
    #single letter
    assert fileformat_replace_pattern("example_$A.txt", 2, "A") == "example_2.txt"
    #more than 1 pattern, what happens?
    assert fileformat_replace_pattern("example_$AA/$A/$B.txt", 2, "A") == "example_02/2/$B.txt"

#To understand how to write down expected output to compare with function output
#We are only interested in <Node> elements that contain coordinates and value at coordinates
#We are not interested into <Param> which contain just configurations?
#Raise exception if node level != 1,2
#Not
def test_get_data_from_warp_xml():
    current_dir = Path(__file__).parent
    xml_file_path = str(current_dir / "test_data" / "TS_017" / "017.xml")

    #Level 1, Angles, integers
    angles = np.array([-52, -50, -48, -46, -44, -42, -40, -38, -36, -34, -32, -30, -28,
           -26, -24, -22, -20, -18, -16, -14, -12, -10, -8, -6, -4, -2,
           0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24,
           26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50,
           52, 54, 56, 58, 60, 62, 64, 66])
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "Angles", 1), angles)
    #Level 1, Dose, floats
    dose = np.array([134.3059 , 132.0675 , 127.5906 , 125.3522 , 118.6369 , 116.3985 ,
       109.6832 , 107.4447 , 100.7294 ,  98.49098,  91.77568,  89.53725,
        82.82195,  80.58351,  73.86821,  71.62978,  64.91447,  62.67604,
        55.96075,  53.72232,  47.00703,  44.7686 ,  38.05331,  35.81488,
        29.09959,  26.86116,  20.14587,  17.90744,  11.19215,   8.95372,
         2.23843,   4.47686,   6.71529,  13.43058,  15.66901,  22.3843 ,
        24.62273,  31.33802,  33.57645,  40.29174,  42.53017,  49.24546,
        51.48389,  58.19918,  60.43761,  67.15291,  69.39134,  76.10664,
        78.34508,  85.06038,  87.29881,  94.01411,  96.25255, 102.9678 ,
       105.2063 , 111.9216 , 114.16   , 120.8753 , 123.1138 , 129.8291 ])
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "Dose", 1), dose)


    #level 2, valid copy-paste node values, try to break it, how?
    nodedatatest = """
            <Node X="0" Y="0" Z="0" Value="-1.463246" />
        		<Node X="1" Y="0" Z="0" Value="5.320158" />
        		<Node X="2" Y="0" Z="0" Value="1.452159" />
        		<Node X="0" Y="1" Z="0" Value="-2.376527" />
        		<Node X="1" Y="1" Z="0" Value="-1.308048" />
        		<Node X="2" Y="1" Z="0" Value="1.455077" />
        		<Node X="0" Y="2" Z="0" Value="0.3901345" />
        		<Node X="1" Y="2" Z="0" Value="-0.5754877" />
        		<Node X="2" Y="2" Z="0" Value="-0.4075638" />
        		<Node X="0" Y="0" Z="1" Value="-0.7106043" />
        		<Node X="1" Y="0" Z="1" Value="5.864784" />
        		<Node X="2" Y="0" Z="1" Value="3.30233" />
        		<Node X="0" Y="1" Z="1" Value="-1.52878" />
        		<Node X="1" Y="1" Z="1" Value="-2.483566" />
        		<Node X="2" Y="1" Z="1" Value="-4.079008" />
        		<Node X="0" Y="2" Z="1" Value="0.2063846" />
        		<Node X="1" Y="2" Z="1" Value="-0.6359377" />
        		<Node X="2" Y="2" Z="1" Value="-0.4039657" />
        		<Node X="0" Y="0" Z="2" Value="-0.4095204" />
        		<Node X="1" Y="0" Z="2" Value="1.397589" />
        		<Node X="2" Y="0" Z="2" Value="0.2903593" />
        		<Node X="0" Y="1" Z="2" Value="0.185078" />
        		<Node X="1" Y="1" Z="2" Value="-1.683118" />
        		<Node X="2" Y="1" Z="2" Value="-2.564194" />
        		<Node X="0" Y="2" Z="2" Value="0.05996355" />
        		<Node X="1" Y="2" Z="2" Value="-0.08808023" />
        		<Node X="2" Y="2" Z="2" Value="0.03305629" />
        		<Node X="0" Y="0" Z="3" Value="-0.5266708" />
        		<Node X="1" Y="0" Z="3" Value="0.4416825" />
        		<Node X="2" Y="0" Z="3" Value="1.395934" />
        		<Node X="0" Y="1" Z="3" Value="-1.08517" />
        		<Node X="1" Y="1" Z="3" Value="-1.230583" />
        		<Node X="2" Y="1" Z="3" Value="-4.273524" />
        		<Node X="0" Y="2" Z="3" Value="0.1407896" />
        		<Node X="1" Y="2" Z="3" Value="0.2722078" />
        		<Node X="2" Y="2" Z="3" Value="0.224728" />
        		<Node X="0" Y="0" Z="4" Value="-0.9587417" />
        		<Node X="1" Y="0" Z="4" Value="-0.2396259" />
        		<Node X="2" Y="0" Z="4" Value="1.009668" />
        		<Node X="0" Y="1" Z="4" Value="-1.290259" />
        		<Node X="1" Y="1" Z="4" Value="-1.248055" />
        		<Node X="2" Y="1" Z="4" Value="-4.197393" />
        		<Node X="0" Y="2" Z="4" Value="0.2185136" />
        		<Node X="1" Y="2" Z="4" Value="-0.2632738" />
        		<Node X="2" Y="2" Z="4" Value="0.06670134" />
        		<Node X="0" Y="0" Z="5" Value="-0.3779781" />
        		<Node X="1" Y="0" Z="5" Value="-1.635345" />
        		<Node X="2" Y="0" Z="5" Value="0.3110349" />
        		<Node X="0" Y="1" Z="5" Value="-0.7143888" />
        		<Node X="1" Y="1" Z="5" Value="-1.022123" />
        		<Node X="2" Y="1" Z="5" Value="-4.777106" />
        		<Node X="0" Y="2" Z="5" Value="0.08590294" />
        		<Node X="1" Y="2" Z="5" Value="0.2265385" />
        		<Node X="2" Y="2" Z="5" Value="0.1821524" />
        		<Node X="0" Y="0" Z="6" Value="-1.530601" />
        		<Node X="1" Y="0" Z="6" Value="-0.5546232" />
        		<Node X="2" Y="0" Z="6" Value="1.850821" />
        		<Node X="0" Y="1" Z="6" Value="-1.653455" />
        		<Node X="1" Y="1" Z="6" Value="-0.7825686" />
        		<Node X="2" Y="1" Z="6" Value="-5.108892" />
        		<Node X="0" Y="2" Z="6" Value="0.3053687" />
        		<Node X="1" Y="2" Z="6" Value="-0.1588862" />
        		<Node X="2" Y="2" Z="6" Value="-0.3030559" />
        		<Node X="0" Y="0" Z="7" Value="-0.3694279" />
        		<Node X="1" Y="0" Z="7" Value="-3.079624" />
        		<Node X="2" Y="0" Z="7" Value="-1.713288" />
        		<Node X="0" Y="1" Z="7" Value="-1.834426" />
        		<Node X="1" Y="1" Z="7" Value="-1.526223" />
        		<Node X="2" Y="1" Z="7" Value="-2.180725" />
        		<Node X="0" Y="2" Z="7" Value="0.1993298" />
        		<Node X="1" Y="2" Z="7" Value="0.3071583" />
        		<Node X="2" Y="2" Z="7" Value="0.3434351" />
        		<Node X="0" Y="0" Z="8" Value="0.7162532" />
        		<Node X="1" Y="0" Z="8" Value="-2.697225" />
        		<Node X="2" Y="0" Z="8" Value="-1.586078" />
        		<Node X="0" Y="1" Z="8" Value="0.321272" />
        		<Node X="1" Y="1" Z="8" Value="-1.675499" />
        		<Node X="2" Y="1" Z="8" Value="-1.831161" />
        		<Node X="0" Y="2" Z="8" Value="-0.1197902" />
        		<Node X="1" Y="2" Z="8" Value="0.3940544" />
        		<Node X="2" Y="2" Z="8" Value="0.3820015" />
        		<Node X="0" Y="0" Z="9" Value="-0.4948481" />
        		<Node X="1" Y="0" Z="9" Value="0.01214749" />
        		<Node X="2" Y="0" Z="9" Value="-1.277677" />
        		<Node X="0" Y="1" Z="9" Value="-2.367667" />
        		<Node X="1" Y="1" Z="9" Value="-2.466241" />
        		<Node X="2" Y="1" Z="9" Value="-2.800977" />
        		<Node X="0" Y="2" Z="9" Value="0.2596546" />
        		<Node X="1" Y="2" Z="9" Value="0.3332871" />
        		<Node X="2" Y="2" Z="9" Value="0.1657559" />
        		<Node X="0" Y="0" Z="10" Value="0.2982151" />
        		<Node X="1" Y="0" Z="10" Value="-1.50164" />
        		<Node X="2" Y="0" Z="10" Value="-1.518515" />
        		<Node X="0" Y="1" Z="10" Value="-0.6211068" />
        		<Node X="1" Y="1" Z="10" Value="-2.937962" />
        		<Node X="2" Y="1" Z="10" Value="-4.469218" />
        		<Node X="0" Y="2" Z="10" Value="0.01148285" />
        		<Node X="1" Y="2" Z="10" Value="0.7165185" />
        		<Node X="2" Y="2" Z="10" Value="0.5784123" />
        		<Node X="0" Y="0" Z="11" Value="-0.5220225" />
        		<Node X="1" Y="0" Z="11" Value="-3.54739" />
        		<Node X="2" Y="0" Z="11" Value="-0.470219" />
        		<Node X="0" Y="1" Z="11" Value="-1.295103" />
        		<Node X="1" Y="1" Z="11" Value="-1.014738" />
        		<Node X="2" Y="1" Z="11" Value="-1.174498" />
        		<Node X="0" Y="2" Z="11" Value="0.1662981" />
        		<Node X="1" Y="2" Z="11" Value="0.4758431" />
        		<Node X="2" Y="2" Z="11" Value="-0.009146304" />
        		<Node X="0" Y="0" Z="12" Value="-1.012112" />
        		<Node X="1" Y="0" Z="12" Value="-3.174333" />
        		<Node X="2" Y="0" Z="12" Value="0.8814076" />
        		<Node X="0" Y="1" Z="12" Value="-1.22106" />
        		<Node X="1" Y="1" Z="12" Value="-1.344784" />
        		<Node X="2" Y="1" Z="12" Value="-3.342522" />
        		<Node X="0" Y="2" Z="12" Value="0.1792351" />
        		<Node X="1" Y="2" Z="12" Value="0.2866584" />
        		<Node X="2" Y="2" Z="12" Value="-0.07647342" />
        		<Node X="0" Y="0" Z="13" Value="-0.4943229" />
        		<Node X="1" Y="0" Z="13" Value="-1.95817" />
        		<Node X="2" Y="0" Z="13" Value="-0.6274569" />
        		<Node X="0" Y="1" Z="13" Value="-1.629542" />
        		<Node X="1" Y="1" Z="13" Value="-1.810308" />
        		<Node X="2" Y="1" Z="13" Value="-2.223524" />
        		<Node X="0" Y="2" Z="13" Value="0.142798" />
        		<Node X="1" Y="2" Z="13" Value="0.5942734" />
        		<Node X="2" Y="2" Z="13" Value="0.3156306" />
        		<Node X="0" Y="0" Z="14" Value="0.1230368" />
        		<Node X="1" Y="0" Z="14" Value="-1.255964" />
        		<Node X="2" Y="0" Z="14" Value="-2.560725" />
        		<Node X="0" Y="1" Z="14" Value="-0.2168628" />
        		<Node X="1" Y="1" Z="14" Value="-2.68361" />
        		<Node X="2" Y="1" Z="14" Value="-2.556492" />
        		<Node X="0" Y="2" Z="14" Value="-0.01003722" />
        		<Node X="1" Y="2" Z="14" Value="0.2361742" />
        		<Node X="2" Y="2" Z="14" Value="0.4976555" />
        		<Node X="0" Y="0" Z="15" Value="-1.611152" />
        		<Node X="1" Y="0" Z="15" Value="-2.151034" />
        		<Node X="2" Y="0" Z="15" Value="-2.108429" />
        		<Node X="0" Y="1" Z="15" Value="-1.768244" />
        		<Node X="1" Y="1" Z="15" Value="-1.228219" />
        		<Node X="2" Y="1" Z="15" Value="-3.732646" />
        		<Node X="0" Y="2" Z="15" Value="0.2576976" />
        		<Node X="1" Y="2" Z="15" Value="0.3873455" />
        		<Node X="2" Y="2" Z="15" Value="0.5294612" />
        		<Node X="0" Y="0" Z="16" Value="-0.6109841" />
        		<Node X="1" Y="0" Z="16" Value="-0.681752" />
        		<Node X="2" Y="0" Z="16" Value="-1.912903" />
        		<Node X="0" Y="1" Z="16" Value="-1.016887" />
        		<Node X="1" Y="1" Z="16" Value="-1.598863" />
        		<Node X="2" Y="1" Z="16" Value="-3.753352" />
        		<Node X="0" Y="2" Z="16" Value="0.1342393" />
        		<Node X="1" Y="2" Z="16" Value="0.2953961" />
        		<Node X="2" Y="2" Z="16" Value="0.2839231" />
        		<Node X="0" Y="0" Z="17" Value="-0.315821" />
        		<Node X="1" Y="0" Z="17" Value="-0.9707435" />
        		<Node X="2" Y="0" Z="17" Value="-0.00040579" />
        		<Node X="0" Y="1" Z="17" Value="-1.032178" />
        		<Node X="1" Y="1" Z="17" Value="-0.2488512" />
        		<Node X="2" Y="1" Z="17" Value="-4.106051" />
        		<Node X="0" Y="2" Z="17" Value="0.1406045" />
        		<Node X="1" Y="2" Z="17" Value="0.1552727" />
        		<Node X="2" Y="2" Z="17" Value="-0.01827077" />
        		<Node X="0" Y="0" Z="18" Value="0.3701774" />
        		<Node X="1" Y="0" Z="18" Value="-1.723352" />
        		<Node X="2" Y="0" Z="18" Value="-1.372155" />
        		<Node X="0" Y="1" Z="18" Value="-0.8536774" />
        		<Node X="1" Y="1" Z="18" Value="-0.56396" />
        		<Node X="2" Y="1" Z="18" Value="-2.582149" />
        		<Node X="0" Y="2" Z="18" Value="0.1191429" />
        		<Node X="1" Y="2" Z="18" Value="0.2179693" />
        		<Node X="2" Y="2" Z="18" Value="-0.07021593" />
        		<Node X="0" Y="0" Z="19" Value="-0.1060382" />
        		<Node X="1" Y="0" Z="19" Value="-1.811532" />
        		<Node X="2" Y="0" Z="19" Value="-1.88311" />
        		<Node X="0" Y="1" Z="19" Value="-0.4577783" />
        		<Node X="1" Y="1" Z="19" Value="-0.09073634" />
        		<Node X="2" Y="1" Z="19" Value="-1.782525" />
        		<Node X="0" Y="2" Z="19" Value="0.06478995" />
        		<Node X="1" Y="2" Z="19" Value="0.2026641" />
        		<Node X="2" Y="2" Z="19" Value="0.09382563" />
        		<Node X="0" Y="0" Z="20" Value="-0.08359869" />
        		<Node X="1" Y="0" Z="20" Value="-0.7033283" />
        		<Node X="2" Y="0" Z="20" Value="-1.705231" />
        		<Node X="0" Y="1" Z="20" Value="-0.3581509" />
        		<Node X="1" Y="1" Z="20" Value="-1.204437" />
        		<Node X="2" Y="1" Z="20" Value="-1.552996" />
        		<Node X="0" Y="2" Z="20" Value="0.03866892" />
        		<Node X="1" Y="2" Z="20" Value="0.06212883" />
        		<Node X="2" Y="2" Z="20" Value="0.1897697" />
        		<Node X="0" Y="0" Z="21" Value="-1.195053" />
        		<Node X="1" Y="0" Z="21" Value="-1.273353" />
        		<Node X="2" Y="0" Z="21" Value="0.1509104" />
        		<Node X="0" Y="1" Z="21" Value="-0.6179267" />
        		<Node X="1" Y="1" Z="21" Value="-0.2443093" />
        		<Node X="2" Y="1" Z="21" Value="-2.65915" />
        		<Node X="0" Y="2" Z="21" Value="0.1130377" />
        		<Node X="1" Y="2" Z="21" Value="-0.0814635" />
        		<Node X="2" Y="2" Z="21" Value="-0.1326908" />
        		<Node X="0" Y="0" Z="22" Value="0.008384475" />
        		<Node X="1" Y="0" Z="22" Value="-1.716682" />
        		<Node X="2" Y="0" Z="22" Value="-1.825313" />
        		<Node X="0" Y="1" Z="22" Value="0.6198087" />
        		<Node X="1" Y="1" Z="22" Value="0.210767" />
        		<Node X="2" Y="1" Z="22" Value="-2.328422" />
        		<Node X="0" Y="2" Z="22" Value="-0.05069068" />
        		<Node X="1" Y="2" Z="22" Value="-0.09321602" />
        		<Node X="2" Y="2" Z="22" Value="-0.009880386" />
        		<Node X="0" Y="0" Z="23" Value="-0.4430967" />
        		<Node X="1" Y="0" Z="23" Value="-1.305517" />
        		<Node X="2" Y="0" Z="23" Value="-1.719509" />
        		<Node X="0" Y="1" Z="23" Value="0.1801253" />
        		<Node X="1" Y="1" Z="23" Value="-0.4872607" />
        		<Node X="2" Y="1" Z="23" Value="-1.736029" />
        		<Node X="0" Y="2" Z="23" Value="-0.01621913" />
        		<Node X="1" Y="2" Z="23" Value="0.04965311" />
        		<Node X="2" Y="2" Z="23" Value="0.1059583" />
        		<Node X="0" Y="0" Z="24" Value="-0.15272" />
        		<Node X="1" Y="0" Z="24" Value="-1.140445" />
        		<Node X="2" Y="0" Z="24" Value="-1.187778" />
        		<Node X="0" Y="1" Z="24" Value="-0.8995698" />
        		<Node X="1" Y="1" Z="24" Value="0.1290679" />
        		<Node X="2" Y="1" Z="24" Value="-2.039777" />
        		<Node X="0" Y="2" Z="24" Value="0.1745232" />
        		<Node X="1" Y="2" Z="24" Value="-0.2871963" />
        		<Node X="2" Y="2" Z="24" Value="-0.1064552" />
        		<Node X="0" Y="0" Z="25" Value="1.473913" />
        		<Node X="1" Y="0" Z="25" Value="-0.6776252" />
        		<Node X="2" Y="0" Z="25" Value="-1.987762" />
        		<Node X="0" Y="1" Z="25" Value="0.2574184" />
        		<Node X="1" Y="1" Z="25" Value="0.1255547" />
        		<Node X="2" Y="1" Z="25" Value="0.2881294" />
        		<Node X="0" Y="2" Z="25" Value="-0.04728567" />
        		<Node X="1" Y="2" Z="25" Value="-0.05159292" />
        		<Node X="2" Y="2" Z="25" Value="-0.11628" />
        		<Node X="0" Y="0" Z="26" Value="0.01599271" />
        		<Node X="1" Y="0" Z="26" Value="-0.463193" />
        		<Node X="2" Y="0" Z="26" Value="-1.147276" />
        		<Node X="0" Y="1" Z="26" Value="2.109198" />
        		<Node X="1" Y="1" Z="26" Value="0.1329704" />
        		<Node X="2" Y="1" Z="26" Value="-1.443648" />
        		<Node X="0" Y="2" Z="26" Value="-0.2384964" />
        		<Node X="1" Y="2" Z="26" Value="-0.1099772" />
        		<Node X="2" Y="2" Z="26" Value="0.3359437" />
        		<Node X="0" Y="0" Z="27" Value="-0.09431294" />
        		<Node X="1" Y="0" Z="27" Value="-0.7216987" />
        		<Node X="2" Y="0" Z="27" Value="-0.4680083" />
        		<Node X="0" Y="1" Z="27" Value="0.6385919" />
        		<Node X="1" Y="1" Z="27" Value="0.2349623" />
        		<Node X="2" Y="1" Z="27" Value="-0.6990215" />
        		<Node X="0" Y="2" Z="27" Value="-0.07671299" />
        		<Node X="1" Y="2" Z="27" Value="-0.1488184" />
        		<Node X="2" Y="2" Z="27" Value="0.1199325" />
        		<Node X="0" Y="0" Z="28" Value="0.06634519" />
        		<Node X="1" Y="0" Z="28" Value="-0.2920912" />
        		<Node X="2" Y="0" Z="28" Value="-0.5589179" />
        		<Node X="0" Y="1" Z="28" Value="1.428783" />
        		<Node X="1" Y="1" Z="28" Value="0.3591155" />
        		<Node X="2" Y="1" Z="28" Value="0.9722123" />
        		<Node X="0" Y="2" Z="28" Value="-0.2322642" />
        		<Node X="1" Y="2" Z="28" Value="0.1640536" />
        		<Node X="2" Y="2" Z="28" Value="0.3133739" />
        		<Node X="0" Y="0" Z="29" Value="0.7822325" />
        		<Node X="1" Y="0" Z="29" Value="0.3300999" />
        		<Node X="2" Y="0" Z="29" Value="-1.627798" />
        		<Node X="0" Y="1" Z="29" Value="-0.1763324" />
        		<Node X="1" Y="1" Z="29" Value="0.6838462" />
        		<Node X="2" Y="1" Z="29" Value="1.724693" />
        		<Node X="0" Y="2" Z="29" Value="-0.00318099" />
        		<Node X="1" Y="2" Z="29" Value="-0.02396142" />
        		<Node X="2" Y="2" Z="29" Value="0.1055321" />
        		<Node X="0" Y="0" Z="30" Value="0.1433068" />
        		<Node X="1" Y="0" Z="30" Value="1.349256" />
        		<Node X="2" Y="0" Z="30" Value="2.26653" />
        		<Node X="0" Y="1" Z="30" Value="1.422405" />
        		<Node X="1" Y="1" Z="30" Value="2.410702" />
        		<Node X="2" Y="1" Z="30" Value="3.195401" />
        		<Node X="0" Y="2" Z="30" Value="-0.2058323" />
        		<Node X="1" Y="2" Z="30" Value="-0.4314051" />
        		<Node X="2" Y="2" Z="30" Value="-0.1900425" />
        		<Node X="0" Y="0" Z="31" Value="-1.179764" />
        		<Node X="1" Y="0" Z="31" Value="0.883917" />
        		<Node X="2" Y="0" Z="31" Value="1.174489" />
        		<Node X="0" Y="1" Z="31" Value="0.09098724" />
        		<Node X="1" Y="1" Z="31" Value="2.660588" />
        		<Node X="2" Y="1" Z="31" Value="2.385371" />
        		<Node X="0" Y="2" Z="31" Value="0.03932115" />
        		<Node X="1" Y="2" Z="31" Value="-0.4811596" />
        		<Node X="2" Y="2" Z="31" Value="-0.1107998" />
        		<Node X="0" Y="0" Z="32" Value="-0.6113384" />
        		<Node X="1" Y="0" Z="32" Value="0.6766121" />
        		<Node X="2" Y="0" Z="32" Value="0.9443513" />
        		<Node X="0" Y="1" Z="32" Value="0.8643097" />
        		<Node X="1" Y="1" Z="32" Value="1.983773" />
        		<Node X="2" Y="1" Z="32" Value="2.509074" />
        		<Node X="0" Y="2" Z="32" Value="-0.1268053" />
        		<Node X="1" Y="2" Z="32" Value="-0.2978492" />
        		<Node X="2" Y="2" Z="32" Value="0.2010989" />
        		<Node X="0" Y="0" Z="33" Value="0.2941595" />
        		<Node X="1" Y="0" Z="33" Value="-0.003231251" />
        		<Node X="2" Y="0" Z="33" Value="0.4881998" />
        		<Node X="0" Y="1" Z="33" Value="1.208933" />
        		<Node X="1" Y="1" Z="33" Value="1.942395" />
        		<Node X="2" Y="1" Z="33" Value="1.338014" />
        		<Node X="0" Y="2" Z="33" Value="-0.1935601" />
        		<Node X="1" Y="2" Z="33" Value="-0.3215258" />
        		<Node X="2" Y="2" Z="33" Value="-0.05696579" />
        		<Node X="0" Y="0" Z="34" Value="-0.3472976" />
        		<Node X="1" Y="0" Z="34" Value="0.09433644" />
        		<Node X="2" Y="0" Z="34" Value="0.3397444" />
        		<Node X="0" Y="1" Z="34" Value="0.127166" />
        		<Node X="1" Y="1" Z="34" Value="1.557775" />
        		<Node X="2" Y="1" Z="34" Value="1.189507" />
        		<Node X="0" Y="2" Z="34" Value="-0.03112097" />
        		<Node X="1" Y="2" Z="34" Value="-0.1582837" />
        		<Node X="2" Y="2" Z="34" Value="0.216153" />
        		<Node X="0" Y="0" Z="35" Value="-0.03777345" />
        		<Node X="1" Y="0" Z="35" Value="-0.4355727" />
        		<Node X="2" Y="0" Z="35" Value="1.36326" />
        		<Node X="0" Y="1" Z="35" Value="0.3529037" />
        		<Node X="1" Y="1" Z="35" Value="1.915063" />
        		<Node X="2" Y="1" Z="35" Value="0.5705025" />
        		<Node X="0" Y="2" Z="35" Value="-0.05825124" />
        		<Node X="1" Y="2" Z="35" Value="-0.1032214" />
        		<Node X="2" Y="2" Z="35" Value="0.3005217" />
        		<Node X="0" Y="0" Z="36" Value="-0.8399256" />
        		<Node X="1" Y="0" Z="36" Value="0.3645122" />
        		<Node X="2" Y="0" Z="36" Value="0.2628777" />
        		<Node X="0" Y="1" Z="36" Value="-0.01787591" />
        		<Node X="1" Y="1" Z="36" Value="1.024429" />
        		<Node X="2" Y="1" Z="36" Value="1.444087" />
        		<Node X="0" Y="2" Z="36" Value="-0.01184748" />
        		<Node X="1" Y="2" Z="36" Value="0.02578417" />
        		<Node X="2" Y="2" Z="36" Value="0.06493462" />
        		<Node X="0" Y="0" Z="37" Value="0.3468409" />
        		<Node X="1" Y="0" Z="37" Value="-0.5145742" />
        		<Node X="2" Y="0" Z="37" Value="0.6361068" />
        		<Node X="0" Y="1" Z="37" Value="1.043736" />
        		<Node X="1" Y="1" Z="37" Value="0.5854191" />
        		<Node X="2" Y="1" Z="37" Value="1.211399" />
        		<Node X="0" Y="2" Z="37" Value="-0.1399718" />
        		<Node X="1" Y="2" Z="37" Value="-0.1381016" />
        		<Node X="2" Y="2" Z="37" Value="-0.1884141" />
        		<Node X="0" Y="0" Z="38" Value="-0.3449529" />
        		<Node X="1" Y="0" Z="38" Value="0.01692064" />
        		<Node X="2" Y="0" Z="38" Value="1.315026" />
        		<Node X="0" Y="1" Z="38" Value="-0.8521376" />
        		<Node X="1" Y="1" Z="38" Value="1.14969" />
        		<Node X="2" Y="1" Z="38" Value="1.065405" />
        		<Node X="0" Y="2" Z="38" Value="0.1287372" />
        		<Node X="1" Y="2" Z="38" Value="-0.2063174" />
        		<Node X="2" Y="2" Z="38" Value="-0.4680429" />
        		<Node X="0" Y="0" Z="39" Value="0.2715719" />
        		<Node X="1" Y="0" Z="39" Value="-0.8855376" />
        		<Node X="2" Y="0" Z="39" Value="3.277173" />
        		<Node X="0" Y="1" Z="39" Value="0.2681186" />
        		<Node X="1" Y="1" Z="39" Value="1.410705" />
        		<Node X="2" Y="1" Z="39" Value="0.6290808" />
        		<Node X="0" Y="2" Z="39" Value="-0.06141897" />
        		<Node X="1" Y="2" Z="39" Value="-0.09191106" />
        		<Node X="2" Y="2" Z="39" Value="-0.04201572" />
        		<Node X="0" Y="0" Z="40" Value="-0.1328561" />
        		<Node X="1" Y="0" Z="40" Value="-0.6741854" />
        		<Node X="2" Y="0" Z="40" Value="0.6705673" />
        		<Node X="0" Y="1" Z="40" Value="-0.525125" />
        		<Node X="1" Y="1" Z="40" Value="1.498924" />
        		<Node X="2" Y="1" Z="40" Value="0.7334902" />
        		<Node X="0" Y="2" Z="40" Value="0.06934692" />
        		<Node X="1" Y="2" Z="40" Value="-0.04914386" />
        		<Node X="2" Y="2" Z="40" Value="-0.4205783" />
        		<Node X="0" Y="0" Z="41" Value="-0.2773003" />
        		<Node X="1" Y="0" Z="41" Value="-0.9362093" />
        		<Node X="2" Y="0" Z="41" Value="-0.2420284" />
        		<Node X="0" Y="1" Z="41" Value="0.0848609" />
        		<Node X="1" Y="1" Z="41" Value="0.489738" />
        		<Node X="2" Y="1" Z="41" Value="1.853848" />
        		<Node X="0" Y="2" Z="41" Value="0.01720244" />
        		<Node X="1" Y="2" Z="41" Value="-0.07237782" />
        		<Node X="2" Y="2" Z="41" Value="-0.4250088" />
        		<Node X="0" Y="0" Z="42" Value="0.5253142" />
        		<Node X="1" Y="0" Z="42" Value="-1.027279" />
        		<Node X="2" Y="0" Z="42" Value="0.1768653" />
        		<Node X="0" Y="1" Z="42" Value="1.107163" />
        		<Node X="1" Y="1" Z="42" Value="1.797172" />
        		<Node X="2" Y="1" Z="42" Value="1.85055" />
        		<Node X="0" Y="2" Z="42" Value="-0.1254745" />
        		<Node X="1" Y="2" Z="42" Value="-0.2504082" />
        		<Node X="2" Y="2" Z="42" Value="-0.2743937" />
        		<Node X="0" Y="0" Z="43" Value="0.1132936" />
        		<Node X="1" Y="0" Z="43" Value="-1.633733" />
        		<Node X="2" Y="0" Z="43" Value="0.5591072" />
        		<Node X="0" Y="1" Z="43" Value="0.7104746" />
        		<Node X="1" Y="1" Z="43" Value="1.830815" />
        		<Node X="2" Y="1" Z="43" Value="1.436787" />
        		<Node X="0" Y="2" Z="43" Value="-0.1145731" />
        		<Node X="1" Y="2" Z="43" Value="0.1250063" />
        		<Node X="2" Y="2" Z="43" Value="-0.157924" />
        		<Node X="0" Y="0" Z="44" Value="-0.349147" />
        		<Node X="1" Y="0" Z="44" Value="0.3923524" />
        		<Node X="2" Y="0" Z="44" Value="-0.2887461" />
        		<Node X="0" Y="1" Z="44" Value="0.1901588" />
        		<Node X="1" Y="1" Z="44" Value="1.04338" />
        		<Node X="2" Y="1" Z="44" Value="1.554292" />
        		<Node X="0" Y="2" Z="44" Value="0.01251187" />
        		<Node X="1" Y="2" Z="44" Value="-0.07875831" />
        		<Node X="2" Y="2" Z="44" Value="-0.3525737" />
        		<Node X="0" Y="0" Z="45" Value="0.2201274" />
        		<Node X="1" Y="0" Z="45" Value="-2.493914" />
        		<Node X="2" Y="0" Z="45" Value="0.7733946" />
        		<Node X="0" Y="1" Z="45" Value="-0.8519823" />
        		<Node X="1" Y="1" Z="45" Value="1.001191" />
        		<Node X="2" Y="1" Z="45" Value="2.241728" />
        		<Node X="0" Y="2" Z="45" Value="0.03651591" />
        		<Node X="1" Y="2" Z="45" Value="0.4484932" />
        		<Node X="2" Y="2" Z="45" Value="-0.06920049" />
        		<Node X="0" Y="0" Z="46" Value="-0.936515" />
        		<Node X="1" Y="0" Z="46" Value="-1.173076" />
        		<Node X="2" Y="0" Z="46" Value="1.238834" />
        		<Node X="0" Y="1" Z="46" Value="0.9181442" />
        		<Node X="1" Y="1" Z="46" Value="1.752505" />
        		<Node X="2" Y="1" Z="46" Value="0.5683882" />
        		<Node X="0" Y="2" Z="46" Value="-0.07035258" />
        		<Node X="1" Y="2" Z="46" Value="0.03659626" />
        		<Node X="2" Y="2" Z="46" Value="-0.02968399" />
        		<Node X="0" Y="0" Z="47" Value="0.1427311" />
        		<Node X="1" Y="0" Z="47" Value="-3.099199" />
        		<Node X="2" Y="0" Z="47" Value="-0.9049471" />
        		<Node X="0" Y="1" Z="47" Value="0.771832" />
        		<Node X="1" Y="1" Z="47" Value="1.965032" />
        		<Node X="2" Y="1" Z="47" Value="1.828468" />
        		<Node X="0" Y="2" Z="47" Value="-0.1411418" />
        		<Node X="1" Y="2" Z="47" Value="0.2229437" />
        		<Node X="2" Y="2" Z="47" Value="0.1171091" />
        		<Node X="0" Y="0" Z="48" Value="0.1909064" />
        		<Node X="1" Y="0" Z="48" Value="0.5024482" />
        		<Node X="2" Y="0" Z="48" Value="1.095386" />
        		<Node X="0" Y="1" Z="48" Value="0.3759831" />
        		<Node X="1" Y="1" Z="48" Value="1.345439" />
        		<Node X="2" Y="1" Z="48" Value="0.6294759" />
        		<Node X="0" Y="2" Z="48" Value="-0.02446398" />
        		<Node X="1" Y="2" Z="48" Value="-0.193266" />
        		<Node X="2" Y="2" Z="48" Value="-0.2045425" />
        		<Node X="0" Y="0" Z="49" Value="0.7162808" />
        		<Node X="1" Y="0" Z="49" Value="-2.214506" />
        		<Node X="2" Y="0" Z="49" Value="0.8649447" />
        		<Node X="0" Y="1" Z="49" Value="1.871275" />
        		<Node X="1" Y="1" Z="49" Value="2.490769" />
        		<Node X="2" Y="1" Z="49" Value="1.605241" />
        		<Node X="0" Y="2" Z="49" Value="-0.2157702" />
        		<Node X="1" Y="2" Z="49" Value="0.0398576" />
        		<Node X="2" Y="2" Z="49" Value="-0.30811" />
        		<Node X="0" Y="0" Z="50" Value="0.538143" />
        		<Node X="1" Y="0" Z="50" Value="-0.8824145" />
        		<Node X="2" Y="0" Z="50" Value="0.01733304" />
        		<Node X="0" Y="1" Z="50" Value="0.04796191" />
        		<Node X="1" Y="1" Z="50" Value="2.129442" />
        		<Node X="2" Y="1" Z="50" Value="2.682483" />
        		<Node X="0" Y="2" Z="50" Value="-0.02275831" />
        		<Node X="1" Y="2" Z="50" Value="-0.329757" />
        		<Node X="2" Y="2" Z="50" Value="-0.4441737" />
        		<Node X="0" Y="0" Z="51" Value="-0.07612614" />
        		<Node X="1" Y="0" Z="51" Value="-2.40694" />
        		<Node X="2" Y="0" Z="51" Value="0.03193626" />
        		<Node X="0" Y="1" Z="51" Value="-0.2932324" />
        		<Node X="1" Y="1" Z="51" Value="2.623614" />
        		<Node X="2" Y="1" Z="51" Value="1.631239" />
        		<Node X="0" Y="2" Z="51" Value="0.0364047" />
        		<Node X="1" Y="2" Z="51" Value="0.1970877" />
        		<Node X="2" Y="2" Z="51" Value="-0.1242779" />
        		<Node X="0" Y="0" Z="52" Value="-0.833669" />
        		<Node X="1" Y="0" Z="52" Value="-1.254515" />
        		<Node X="2" Y="0" Z="52" Value="-0.168173" />
        		<Node X="0" Y="1" Z="52" Value="-2.982485" />
        		<Node X="1" Y="1" Z="52" Value="3.099726" />
        		<Node X="2" Y="1" Z="52" Value="2.312814" />
        		<Node X="0" Y="2" Z="52" Value="0.2808829" />
        		<Node X="1" Y="2" Z="52" Value="0.2039993" />
        		<Node X="2" Y="2" Z="52" Value="-0.0898677" />
        		<Node X="0" Y="0" Z="53" Value="-0.3158733" />
        		<Node X="1" Y="0" Z="53" Value="-2.156559" />
        		<Node X="2" Y="0" Z="53" Value="2.417242" />
        		<Node X="0" Y="1" Z="53" Value="-1.047516" />
        		<Node X="1" Y="1" Z="53" Value="3.627437" />
        		<Node X="2" Y="1" Z="53" Value="1.944811" />
        		<Node X="0" Y="2" Z="53" Value="0.09728091" />
        		<Node X="1" Y="2" Z="53" Value="0.1532321" />
        		<Node X="2" Y="2" Z="53" Value="-0.6192255" />
        		<Node X="0" Y="0" Z="54" Value="-0.04899749" />
        		<Node X="1" Y="0" Z="54" Value="2.848426" />
        		<Node X="2" Y="0" Z="54" Value="0.2904806" />
        		<Node X="0" Y="1" Z="54" Value="-2.252651" />
        		<Node X="1" Y="1" Z="54" Value="2.962822" />
        		<Node X="2" Y="1" Z="54" Value="3.871899" />
        		<Node X="0" Y="2" Z="54" Value="0.1288705" />
        		<Node X="1" Y="2" Z="54" Value="-0.09419243" />
        		<Node X="2" Y="2" Z="54" Value="-0.1377179" />
        		<Node X="0" Y="0" Z="55" Value="0.8474329" />
        		<Node X="1" Y="0" Z="55" Value="1.214333" />
        		<Node X="2" Y="0" Z="55" Value="-0.52802" />
        		<Node X="0" Y="1" Z="55" Value="-0.4807324" />
        		<Node X="1" Y="1" Z="55" Value="4.788553" />
        		<Node X="2" Y="1" Z="55" Value="0.5269803" />
        		<Node X="0" Y="2" Z="55" Value="-0.134818" />
        		<Node X="1" Y="2" Z="55" Value="-0.2000996" />
        		<Node X="2" Y="2" Z="55" Value="0.07953535" />
        		<Node X="0" Y="0" Z="56" Value="0.1961866" />
        		<Node X="1" Y="0" Z="56" Value="0.630663" />
        		<Node X="2" Y="0" Z="56" Value="-1.200837" />
        		<Node X="0" Y="1" Z="56" Value="-1.504695" />
        		<Node X="1" Y="1" Z="56" Value="4.681966" />
        		<Node X="2" Y="1" Z="56" Value="3.99545" />
        		<Node X="0" Y="2" Z="56" Value="0.05390552" />
        		<Node X="1" Y="2" Z="56" Value="-0.2746132" />
        		<Node X="2" Y="2" Z="56" Value="0.09590138" />
        		<Node X="0" Y="0" Z="57" Value="-0.192025" />
        		<Node X="1" Y="0" Z="57" Value="2.120564" />
        		<Node X="2" Y="0" Z="57" Value="-0.5196728" />
        		<Node X="0" Y="1" Z="57" Value="-2.184315" />
        		<Node X="1" Y="1" Z="57" Value="3.931082" />
        		<Node X="2" Y="1" Z="57" Value="4.095085" />
        		<Node X="0" Y="2" Z="57" Value="0.1436728" />
        		<Node X="1" Y="2" Z="57" Value="-0.6218677" />
        		<Node X="2" Y="2" Z="57" Value="0.02701958" />
        		<Node X="0" Y="0" Z="58" Value="0.6309627" />
        		<Node X="1" Y="0" Z="58" Value="-0.869297" />
        		<Node X="2" Y="0" Z="58" Value="0.2767608" />
        		<Node X="0" Y="1" Z="58" Value="1.617473" />
        		<Node X="1" Y="1" Z="58" Value="5.58949" />
        		<Node X="2" Y="1" Z="58" Value="6.701704" />
        		<Node X="0" Y="2" Z="58" Value="-0.2136974" />
        		<Node X="1" Y="2" Z="58" Value="-0.151066" />
        		<Node X="2" Y="2" Z="58" Value="-0.08292479" />
        		<Node X="0" Y="0" Z="59" Value="-0.1033018" />
        		<Node X="1" Y="0" Z="59" Value="-0.8923529" />
        		<Node X="2" Y="0" Z="59" Value="1.542079" />
        		<Node X="0" Y="1" Z="59" Value="-0.8160006" />
        		<Node X="1" Y="1" Z="59" Value="3.976453" />
        		<Node X="2" Y="1" Z="59" Value="7.305612" />
        		<Node X="0" Y="2" Z="59" Value="0.0611175" />
        		<Node X="1" Y="2" Z="59" Value="-0.1232658" />
        		<Node X="2" Y="2" Z="59" Value="-0.6120446" />
        		"""
    grid_movement_x = []
    for line in nodedatatest.strip().split("\n"):
        start = line.find('Value="') + len('Value="')
        end = line.find('"', start)
        value = float(line[start:end])
        grid_movement_x.append(value)
    grid_movement_x = np.asarray(grid_movement_x)
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "GridMovementX", 2), grid_movement_x)

    #level2, wrong(not correct) node values
    nodedatatest1 = """ 
    <Node X="0" Y="0" Z="0" Value="0" /> ###Wrong value
        		<Node X="1" Y="0" Z="0" Value="5.320158" />
        		<Node X="2" Y="0" Z="0" Value="1.452159" />
        		<Node X="0" Y="1" Z="0" Value="-2.376527" />
        		<Node X="1" Y="1" Z="0" Value="-1.308048" />
        		<Node X="2" Y="1" Z="0" Value="1.455077" />
        		<Node X="0" Y="2" Z="0" Value="0.3901345" />
        		<Node X="1" Y="2" Z="0" Value="-0.5754877" />
        		<Node X="2" Y="2" Z="0" Value="-0.4075638" />
        		<Node X="0" Y="0" Z="1" Value="-0.7106043" />
        		<Node X="1" Y="0" Z="1" Value="5.864784" />
        		<Node X="2" Y="0" Z="1" Value="3.30233" />
        		<Node X="0" Y="1" Z="1" Value="-1.52878" />
        		<Node X="1" Y="1" Z="1" Value="-2.483566" />
        		<Node X="2" Y="1" Z="1" Value="-4.079008" />
        		<Node X="0" Y="2" Z="1" Value="0.2063846" />
        		<Node X="1" Y="2" Z="1" Value="-0.6359377" />
        		<Node X="2" Y="2" Z="1" Value="-0.4039657" />
        		<Node X="0" Y="0" Z="2" Value="-0.4095204" />
        		<Node X="1" Y="0" Z="2" Value="1.397589" />
        		<Node X="2" Y="0" Z="2" Value="0.2903593" />
        		<Node X="0" Y="1" Z="2" Value="0.185078" />
        		<Node X="1" Y="1" Z="2" Value="-1.683118" />
        		<Node X="2" Y="1" Z="2" Value="-2.564194" />
        		<Node X="0" Y="2" Z="2" Value="0.05996355" />
        		<Node X="1" Y="2" Z="2" Value="-0.08808023" />
        		<Node X="2" Y="2" Z="2" Value="0.03305629" />
        		<Node X="0" Y="0" Z="3" Value="-0.5266708" />
        		<Node X="1" Y="0" Z="3" Value="0.4416825" />
        		<Node X="2" Y="0" Z="3" Value="1.395934" />
        		<Node X="0" Y="1" Z="3" Value="-1.08517" />
        		<Node X="1" Y="1" Z="3" Value="-1.230583" />
        		<Node X="2" Y="1" Z="3" Value="-4.273524" />
        		<Node X="0" Y="2" Z="3" Value="0.1407896" />
        		<Node X="1" Y="2" Z="3" Value="0.2722078" />
        		<Node X="2" Y="2" Z="3" Value="0.224728" />
        		<Node X="0" Y="0" Z="4" Value="-0.9587417" />
        		<Node X="1" Y="0" Z="4" Value="-0.2396259" />
        		<Node X="2" Y="0" Z="4" Value="1.009668" />
        		<Node X="0" Y="1" Z="4" Value="-1.290259" />
        		<Node X="1" Y="1" Z="4" Value="-1.248055" />
        		<Node X="2" Y="1" Z="4" Value="-4.197393" />
        		<Node X="0" Y="2" Z="4" Value="0.2185136" />
        		<Node X="1" Y="2" Z="4" Value="-0.2632738" />
        		<Node X="2" Y="2" Z="4" Value="0.06670134" />
        		<Node X="0" Y="0" Z="5" Value="-0.3779781" />
        		<Node X="1" Y="0" Z="5" Value="-1.635345" />
        		<Node X="2" Y="0" Z="5" Value="0.3110349" />
        		<Node X="0" Y="1" Z="5" Value="-0.7143888" />
        		<Node X="1" Y="1" Z="5" Value="-1.022123" />
        		<Node X="2" Y="1" Z="5" Value="-4.777106" />
        		<Node X="0" Y="2" Z="5" Value="0.08590294" />
        		<Node X="1" Y="2" Z="5" Value="0.2265385" />
        		<Node X="2" Y="2" Z="5" Value="0.1821524" />
        		<Node X="0" Y="0" Z="6" Value="-1.530601" />
        		<Node X="1" Y="0" Z="6" Value="-0.5546232" />
        		<Node X="2" Y="0" Z="6" Value="1.850821" />
        		<Node X="0" Y="1" Z="6" Value="-1.653455" />
        		<Node X="1" Y="1" Z="6" Value="-0.7825686" />
        		<Node X="2" Y="1" Z="6" Value="-5.108892" />
        		<Node X="0" Y="2" Z="6" Value="0.3053687" />
        		<Node X="1" Y="2" Z="6" Value="-0.1588862" />
        		<Node X="2" Y="2" Z="6" Value="-0.3030559" />
        		<Node X="0" Y="0" Z="7" Value="-0.3694279" />
        		<Node X="1" Y="0" Z="7" Value="-3.079624" />
        		<Node X="2" Y="0" Z="7" Value="-1.713288" />
        		<Node X="0" Y="1" Z="7" Value="-1.834426" />
        		<Node X="1" Y="1" Z="7" Value="-1.526223" />
        		<Node X="2" Y="1" Z="7" Value="-2.180725" />
        		<Node X="0" Y="2" Z="7" Value="0.1993298" />
        		<Node X="1" Y="2" Z="7" Value="0.3071583" />
        		<Node X="2" Y="2" Z="7" Value="0.3434351" />
        		<Node X="0" Y="0" Z="8" Value="0.7162532" />
        		<Node X="1" Y="0" Z="8" Value="-2.697225" />
        		<Node X="2" Y="0" Z="8" Value="-1.586078" />
        		<Node X="0" Y="1" Z="8" Value="0.321272" />
        		<Node X="1" Y="1" Z="8" Value="-1.675499" />
        		<Node X="2" Y="1" Z="8" Value="-1.831161" />
        		<Node X="0" Y="2" Z="8" Value="-0.1197902" />
        		<Node X="1" Y="2" Z="8" Value="0.3940544" />
        		<Node X="2" Y="2" Z="8" Value="0.3820015" />
        		<Node X="0" Y="0" Z="9" Value="-0.4948481" />
        		<Node X="1" Y="0" Z="9" Value="0.01214749" />
        		<Node X="2" Y="0" Z="9" Value="-1.277677" />
        		<Node X="0" Y="1" Z="9" Value="-2.367667" />
        		<Node X="1" Y="1" Z="9" Value="-2.466241" />
        		<Node X="2" Y="1" Z="9" Value="-2.800977" />
        		<Node X="0" Y="2" Z="9" Value="0.2596546" />
        		<Node X="1" Y="2" Z="9" Value="0.3332871" />
        		<Node X="2" Y="2" Z="9" Value="0.1657559" />
        		<Node X="0" Y="0" Z="10" Value="0.2982151" />
        		<Node X="1" Y="0" Z="10" Value="-1.50164" />
        		<Node X="2" Y="0" Z="10" Value="-1.518515" />
        		<Node X="0" Y="1" Z="10" Value="-0.6211068" />
        		<Node X="1" Y="1" Z="10" Value="-2.937962" />
        		<Node X="2" Y="1" Z="10" Value="-4.469218" />
        		<Node X="0" Y="2" Z="10" Value="0.01148285" />
        		<Node X="1" Y="2" Z="10" Value="0.7165185" />
        		<Node X="2" Y="2" Z="10" Value="0.5784123" />
        		<Node X="0" Y="0" Z="11" Value="-0.5220225" />
        		<Node X="1" Y="0" Z="11" Value="-3.54739" />
        		<Node X="2" Y="0" Z="11" Value="-0.470219" />
        		<Node X="0" Y="1" Z="11" Value="-1.295103" />
        		<Node X="1" Y="1" Z="11" Value="-1.014738" />
        		<Node X="2" Y="1" Z="11" Value="-1.174498" />
        		<Node X="0" Y="2" Z="11" Value="0.1662981" />
        		<Node X="1" Y="2" Z="11" Value="0.4758431" />
        		<Node X="2" Y="2" Z="11" Value="-0.009146304" />
        		<Node X="0" Y="0" Z="12" Value="-1.012112" />
        		<Node X="1" Y="0" Z="12" Value="-3.174333" />
        		<Node X="2" Y="0" Z="12" Value="0.8814076" />
        		<Node X="0" Y="1" Z="12" Value="-1.22106" />
        		<Node X="1" Y="1" Z="12" Value="-1.344784" />
        		<Node X="2" Y="1" Z="12" Value="-3.342522" />
        		<Node X="0" Y="2" Z="12" Value="0.1792351" />
        		<Node X="1" Y="2" Z="12" Value="0.2866584" />
        		<Node X="2" Y="2" Z="12" Value="-0.07647342" />
        		<Node X="0" Y="0" Z="13" Value="-0.4943229" />
        		<Node X="1" Y="0" Z="13" Value="-1.95817" />
        		<Node X="2" Y="0" Z="13" Value="-0.6274569" />
        		<Node X="0" Y="1" Z="13" Value="-1.629542" />
        		<Node X="1" Y="1" Z="13" Value="-1.810308" />
        		<Node X="2" Y="1" Z="13" Value="-2.223524" />
        		<Node X="0" Y="2" Z="13" Value="0.142798" />
        		<Node X="1" Y="2" Z="13" Value="0.5942734" />
        		<Node X="2" Y="2" Z="13" Value="0.3156306" />
        		<Node X="0" Y="0" Z="14" Value="0.1230368" />
        		<Node X="1" Y="0" Z="14" Value="-1.255964" />
        		<Node X="2" Y="0" Z="14" Value="-2.560725" />
        		<Node X="0" Y="1" Z="14" Value="-0.2168628" />
        		<Node X="1" Y="1" Z="14" Value="-2.68361" />
        		<Node X="2" Y="1" Z="14" Value="-2.556492" />
        		<Node X="0" Y="2" Z="14" Value="-0.01003722" />
        		<Node X="1" Y="2" Z="14" Value="0.2361742" />
        		<Node X="2" Y="2" Z="14" Value="0.4976555" />
        		<Node X="0" Y="0" Z="15" Value="-1.611152" />
        		<Node X="1" Y="0" Z="15" Value="-2.151034" />
        		<Node X="2" Y="0" Z="15" Value="-2.108429" />
        		<Node X="0" Y="1" Z="15" Value="-1.768244" />
        		<Node X="1" Y="1" Z="15" Value="-1.228219" />
        		<Node X="2" Y="1" Z="15" Value="-3.732646" />
        		<Node X="0" Y="2" Z="15" Value="0.2576976" />
        		<Node X="1" Y="2" Z="15" Value="0.3873455" />
        		<Node X="2" Y="2" Z="15" Value="0.5294612" />
        		<Node X="0" Y="0" Z="16" Value="-0.6109841" />
        		<Node X="1" Y="0" Z="16" Value="-0.681752" />
        		<Node X="2" Y="0" Z="16" Value="-1.912903" />
        		<Node X="0" Y="1" Z="16" Value="-1.016887" />
        		<Node X="1" Y="1" Z="16" Value="-1.598863" />
        		<Node X="2" Y="1" Z="16" Value="-3.753352" />
        		<Node X="0" Y="2" Z="16" Value="0.1342393" />
        		<Node X="1" Y="2" Z="16" Value="0.2953961" />
        		<Node X="2" Y="2" Z="16" Value="0.2839231" />
        		<Node X="0" Y="0" Z="17" Value="-0.315821" />
        		<Node X="1" Y="0" Z="17" Value="-0.9707435" />
        		<Node X="2" Y="0" Z="17" Value="-0.00040579" />
        		<Node X="0" Y="1" Z="17" Value="-1.032178" />
        		<Node X="1" Y="1" Z="17" Value="-0.2488512" />
        		<Node X="2" Y="1" Z="17" Value="-4.106051" />
        		<Node X="0" Y="2" Z="17" Value="0.1406045" />
        		<Node X="1" Y="2" Z="17" Value="0.1552727" />
        		<Node X="2" Y="2" Z="17" Value="-0.01827077" />
        		<Node X="0" Y="0" Z="18" Value="0.3701774" />
        		<Node X="1" Y="0" Z="18" Value="-1.723352" />
        		<Node X="2" Y="0" Z="18" Value="-1.372155" />
        		<Node X="0" Y="1" Z="18" Value="-0.8536774" />
        		<Node X="1" Y="1" Z="18" Value="-0.56396" />
        		<Node X="2" Y="1" Z="18" Value="-2.582149" />
        		<Node X="0" Y="2" Z="18" Value="0.1191429" />
        		<Node X="1" Y="2" Z="18" Value="0.2179693" />
        		<Node X="2" Y="2" Z="18" Value="-0.07021593" />
        		<Node X="0" Y="0" Z="19" Value="-0.1060382" />
        		<Node X="1" Y="0" Z="19" Value="-1.811532" />
        		<Node X="2" Y="0" Z="19" Value="-1.88311" />
        		<Node X="0" Y="1" Z="19" Value="-0.4577783" />
        		<Node X="1" Y="1" Z="19" Value="-0.09073634" />
        		<Node X="2" Y="1" Z="19" Value="-1.782525" />
        		<Node X="0" Y="2" Z="19" Value="0.06478995" />
        		<Node X="1" Y="2" Z="19" Value="0.2026641" />
        		<Node X="2" Y="2" Z="19" Value="0.09382563" />
        		<Node X="0" Y="0" Z="20" Value="-0.08359869" />
        		<Node X="1" Y="0" Z="20" Value="-0.7033283" />
        		<Node X="2" Y="0" Z="20" Value="-1.705231" />
        		<Node X="0" Y="1" Z="20" Value="-0.3581509" />
        		<Node X="1" Y="1" Z="20" Value="-1.204437" />
        		<Node X="2" Y="1" Z="20" Value="-1.552996" />
        		<Node X="0" Y="2" Z="20" Value="0.03866892" />
        		<Node X="1" Y="2" Z="20" Value="0.06212883" />
        		<Node X="2" Y="2" Z="20" Value="0.1897697" />
        		<Node X="0" Y="0" Z="21" Value="-1.195053" />
        		<Node X="1" Y="0" Z="21" Value="-1.273353" />
        		<Node X="2" Y="0" Z="21" Value="0.1509104" />
        		<Node X="0" Y="1" Z="21" Value="-0.6179267" />
        		<Node X="1" Y="1" Z="21" Value="-0.2443093" />
        		<Node X="2" Y="1" Z="21" Value="-2.65915" />
        		<Node X="0" Y="2" Z="21" Value="0.1130377" />
        		<Node X="1" Y="2" Z="21" Value="-0.0814635" />
        		<Node X="2" Y="2" Z="21" Value="-0.1326908" />
        		<Node X="0" Y="0" Z="22" Value="0.008384475" />
        		<Node X="1" Y="0" Z="22" Value="-1.716682" />
        		<Node X="2" Y="0" Z="22" Value="-1.825313" />
        		<Node X="0" Y="1" Z="22" Value="0.6198087" />
        		<Node X="1" Y="1" Z="22" Value="0.210767" />
        		<Node X="2" Y="1" Z="22" Value="-2.328422" />
        		<Node X="0" Y="2" Z="22" Value="-0.05069068" />
        		<Node X="1" Y="2" Z="22" Value="-0.09321602" />
        		<Node X="2" Y="2" Z="22" Value="-0.009880386" />
        		<Node X="0" Y="0" Z="23" Value="-0.4430967" />
        		<Node X="1" Y="0" Z="23" Value="-1.305517" />
        		<Node X="2" Y="0" Z="23" Value="-1.719509" />
        		<Node X="0" Y="1" Z="23" Value="0.1801253" />
        		<Node X="1" Y="1" Z="23" Value="-0.4872607" />
        		<Node X="2" Y="1" Z="23" Value="-1.736029" />
        		<Node X="0" Y="2" Z="23" Value="-0.01621913" />
        		<Node X="1" Y="2" Z="23" Value="0.04965311" />
        		<Node X="2" Y="2" Z="23" Value="0.1059583" />
        		<Node X="0" Y="0" Z="24" Value="-0.15272" />
        		<Node X="1" Y="0" Z="24" Value="-1.140445" />
        		<Node X="2" Y="0" Z="24" Value="-1.187778" />
        		<Node X="0" Y="1" Z="24" Value="-0.8995698" />
        		<Node X="1" Y="1" Z="24" Value="0.1290679" />
        		<Node X="2" Y="1" Z="24" Value="-2.039777" />
        		<Node X="0" Y="2" Z="24" Value="0.1745232" />
        		<Node X="1" Y="2" Z="24" Value="-0.2871963" />
        		<Node X="2" Y="2" Z="24" Value="-0.1064552" />
        		<Node X="0" Y="0" Z="25" Value="1.473913" />
        		<Node X="1" Y="0" Z="25" Value="-0.6776252" />
        		<Node X="2" Y="0" Z="25" Value="-1.987762" />
        		<Node X="0" Y="1" Z="25" Value="0.2574184" />
        		<Node X="1" Y="1" Z="25" Value="0.1255547" />
        		<Node X="2" Y="1" Z="25" Value="0.2881294" />
        		<Node X="0" Y="2" Z="25" Value="-0.04728567" />
        		<Node X="1" Y="2" Z="25" Value="-0.05159292" />
        		<Node X="2" Y="2" Z="25" Value="-0.11628" />
        		<Node X="0" Y="0" Z="26" Value="0.01599271" />
        		<Node X="1" Y="0" Z="26" Value="-0.463193" />
        		<Node X="2" Y="0" Z="26" Value="-1.147276" />
        		<Node X="0" Y="1" Z="26" Value="2.109198" />
        		<Node X="1" Y="1" Z="26" Value="0.1329704" />
        		<Node X="2" Y="1" Z="26" Value="-1.443648" />
        		<Node X="0" Y="2" Z="26" Value="-0.2384964" />
        		<Node X="1" Y="2" Z="26" Value="-0.1099772" />
        		<Node X="2" Y="2" Z="26" Value="0.3359437" />
        		<Node X="0" Y="0" Z="27" Value="-0.09431294" />
        		<Node X="1" Y="0" Z="27" Value="-0.7216987" />
        		<Node X="2" Y="0" Z="27" Value="-0.4680083" />
        		<Node X="0" Y="1" Z="27" Value="0.6385919" />
        		<Node X="1" Y="1" Z="27" Value="0.2349623" />
        		<Node X="2" Y="1" Z="27" Value="-0.6990215" />
        		<Node X="0" Y="2" Z="27" Value="-0.07671299" />
        		<Node X="1" Y="2" Z="27" Value="-0.1488184" />
        		<Node X="2" Y="2" Z="27" Value="0.1199325" />
        		<Node X="0" Y="0" Z="28" Value="0.06634519" />
        		<Node X="1" Y="0" Z="28" Value="-0.2920912" />
        		<Node X="2" Y="0" Z="28" Value="-0.5589179" />
        		<Node X="0" Y="1" Z="28" Value="1.428783" />
        		<Node X="1" Y="1" Z="28" Value="0.3591155" />
        		<Node X="2" Y="1" Z="28" Value="0.9722123" />
        		<Node X="0" Y="2" Z="28" Value="-0.2322642" />
        		<Node X="1" Y="2" Z="28" Value="0.1640536" />
        		<Node X="2" Y="2" Z="28" Value="0.3133739" />
        		<Node X="0" Y="0" Z="29" Value="0.7822325" />
        		<Node X="1" Y="0" Z="29" Value="0.3300999" />
        		<Node X="2" Y="0" Z="29" Value="-1.627798" />
        		<Node X="0" Y="1" Z="29" Value="-0.1763324" />
        		<Node X="1" Y="1" Z="29" Value="0.6838462" />
        		<Node X="2" Y="1" Z="29" Value="1.724693" />
        		<Node X="0" Y="2" Z="29" Value="-0.00318099" />
        		<Node X="1" Y="2" Z="29" Value="-0.02396142" />
        		<Node X="2" Y="2" Z="29" Value="0.1055321" />
        		<Node X="0" Y="0" Z="30" Value="0.1433068" />
        		<Node X="1" Y="0" Z="30" Value="1.349256" />
        		<Node X="2" Y="0" Z="30" Value="2.26653" />
        		<Node X="0" Y="1" Z="30" Value="1.422405" />
        		<Node X="1" Y="1" Z="30" Value="2.410702" />
        		<Node X="2" Y="1" Z="30" Value="3.195401" />
        		<Node X="0" Y="2" Z="30" Value="-0.2058323" />
        		<Node X="1" Y="2" Z="30" Value="-0.4314051" />
        		<Node X="2" Y="2" Z="30" Value="-0.1900425" />
        		<Node X="0" Y="0" Z="31" Value="-1.179764" />
        		<Node X="1" Y="0" Z="31" Value="0.883917" />
        		<Node X="2" Y="0" Z="31" Value="1.174489" />
        		<Node X="0" Y="1" Z="31" Value="0.09098724" />
        		<Node X="1" Y="1" Z="31" Value="2.660588" />
        		<Node X="2" Y="1" Z="31" Value="2.385371" />
        		<Node X="0" Y="2" Z="31" Value="0.03932115" />
        		<Node X="1" Y="2" Z="31" Value="-0.4811596" />
        		<Node X="2" Y="2" Z="31" Value="-0.1107998" />
        		<Node X="0" Y="0" Z="32" Value="-0.6113384" />
        		<Node X="1" Y="0" Z="32" Value="0.6766121" />
        		<Node X="2" Y="0" Z="32" Value="0.9443513" />
        		<Node X="0" Y="1" Z="32" Value="0.8643097" />
        		<Node X="1" Y="1" Z="32" Value="1.983773" />
        		<Node X="2" Y="1" Z="32" Value="2.509074" />
        		<Node X="0" Y="2" Z="32" Value="-0.1268053" />
        		<Node X="1" Y="2" Z="32" Value="-0.2978492" />
        		<Node X="2" Y="2" Z="32" Value="0.2010989" />
        		<Node X="0" Y="0" Z="33" Value="0.2941595" />
        		<Node X="1" Y="0" Z="33" Value="-0.003231251" />
        		<Node X="2" Y="0" Z="33" Value="0.4881998" />
        		<Node X="0" Y="1" Z="33" Value="1.208933" />
        		<Node X="1" Y="1" Z="33" Value="1.942395" />
        		<Node X="2" Y="1" Z="33" Value="1.338014" />
        		<Node X="0" Y="2" Z="33" Value="-0.1935601" />
        		<Node X="1" Y="2" Z="33" Value="-0.3215258" />
        		<Node X="2" Y="2" Z="33" Value="-0.05696579" />
        		<Node X="0" Y="0" Z="34" Value="-0.3472976" />
        		<Node X="1" Y="0" Z="34" Value="0.09433644" />
        		<Node X="2" Y="0" Z="34" Value="0.3397444" />
        		<Node X="0" Y="1" Z="34" Value="0.127166" />
        		<Node X="1" Y="1" Z="34" Value="1.557775" />
        		<Node X="2" Y="1" Z="34" Value="1.189507" />
        		<Node X="0" Y="2" Z="34" Value="-0.03112097" />
        		<Node X="1" Y="2" Z="34" Value="-0.1582837" />
        		<Node X="2" Y="2" Z="34" Value="0.216153" />
        		<Node X="0" Y="0" Z="35" Value="-0.03777345" />
        		<Node X="1" Y="0" Z="35" Value="-0.4355727" />
        		<Node X="2" Y="0" Z="35" Value="1.36326" />
        		<Node X="0" Y="1" Z="35" Value="0.3529037" />
        		<Node X="1" Y="1" Z="35" Value="1.915063" />
        		<Node X="2" Y="1" Z="35" Value="0.5705025" />
        		<Node X="0" Y="2" Z="35" Value="-0.05825124" />
        		<Node X="1" Y="2" Z="35" Value="-0.1032214" />
        		<Node X="2" Y="2" Z="35" Value="0.3005217" />
        		<Node X="0" Y="0" Z="36" Value="-0.8399256" />
        		<Node X="1" Y="0" Z="36" Value="0.3645122" />
        		<Node X="2" Y="0" Z="36" Value="0.2628777" />
        		<Node X="0" Y="1" Z="36" Value="-0.01787591" />
        		<Node X="1" Y="1" Z="36" Value="1.024429" />
        		<Node X="2" Y="1" Z="36" Value="1.444087" />
        		<Node X="0" Y="2" Z="36" Value="-0.01184748" />
        		<Node X="1" Y="2" Z="36" Value="0.02578417" />
        		<Node X="2" Y="2" Z="36" Value="0.06493462" />
        		<Node X="0" Y="0" Z="37" Value="0.3468409" />
        		<Node X="1" Y="0" Z="37" Value="-0.5145742" />
        		<Node X="2" Y="0" Z="37" Value="0.6361068" />
        		<Node X="0" Y="1" Z="37" Value="1.043736" />
        		<Node X="1" Y="1" Z="37" Value="0.5854191" />
        		<Node X="2" Y="1" Z="37" Value="1.211399" />
        		<Node X="0" Y="2" Z="37" Value="-0.1399718" />
        		<Node X="1" Y="2" Z="37" Value="-0.1381016" />
        		<Node X="2" Y="2" Z="37" Value="-0.1884141" />
        		<Node X="0" Y="0" Z="38" Value="-0.3449529" />
        		<Node X="1" Y="0" Z="38" Value="0.01692064" />
        		<Node X="2" Y="0" Z="38" Value="1.315026" />
        		<Node X="0" Y="1" Z="38" Value="-0.8521376" />
        		<Node X="1" Y="1" Z="38" Value="1.14969" />
        		<Node X="2" Y="1" Z="38" Value="1.065405" />
        		<Node X="0" Y="2" Z="38" Value="0.1287372" />
        		<Node X="1" Y="2" Z="38" Value="-0.2063174" />
        		<Node X="2" Y="2" Z="38" Value="-0.4680429" />
        		<Node X="0" Y="0" Z="39" Value="0.2715719" />
        		<Node X="1" Y="0" Z="39" Value="-0.8855376" />
        		<Node X="2" Y="0" Z="39" Value="3.277173" />
        		<Node X="0" Y="1" Z="39" Value="0.2681186" />
        		<Node X="1" Y="1" Z="39" Value="1.410705" />
        		<Node X="2" Y="1" Z="39" Value="0.6290808" />
        		<Node X="0" Y="2" Z="39" Value="-0.06141897" />
        		<Node X="1" Y="2" Z="39" Value="-0.09191106" />
        		<Node X="2" Y="2" Z="39" Value="-0.04201572" />
        		<Node X="0" Y="0" Z="40" Value="-0.1328561" />
        		<Node X="1" Y="0" Z="40" Value="-0.6741854" />
        		<Node X="2" Y="0" Z="40" Value="0.6705673" />
        		<Node X="0" Y="1" Z="40" Value="-0.525125" />
        		<Node X="1" Y="1" Z="40" Value="1.498924" />
        		<Node X="2" Y="1" Z="40" Value="0.7334902" />
        		<Node X="0" Y="2" Z="40" Value="0.06934692" />
        		<Node X="1" Y="2" Z="40" Value="-0.04914386" />
        		<Node X="2" Y="2" Z="40" Value="-0.4205783" />
        		<Node X="0" Y="0" Z="41" Value="-0.2773003" />
        		<Node X="1" Y="0" Z="41" Value="-0.9362093" />
        		<Node X="2" Y="0" Z="41" Value="-0.2420284" />
        		<Node X="0" Y="1" Z="41" Value="0.0848609" />
        		<Node X="1" Y="1" Z="41" Value="0.489738" />
        		<Node X="2" Y="1" Z="41" Value="1.853848" />
        		<Node X="0" Y="2" Z="41" Value="0.01720244" />
        		<Node X="1" Y="2" Z="41" Value="-0.07237782" />
        		<Node X="2" Y="2" Z="41" Value="-0.4250088" />
        		<Node X="0" Y="0" Z="42" Value="0.5253142" />
        		<Node X="1" Y="0" Z="42" Value="-1.027279" />
        		<Node X="2" Y="0" Z="42" Value="0.1768653" />
        		<Node X="0" Y="1" Z="42" Value="1.107163" />
        		<Node X="1" Y="1" Z="42" Value="1.797172" />
        		<Node X="2" Y="1" Z="42" Value="1.85055" />
        		<Node X="0" Y="2" Z="42" Value="-0.1254745" />
        		<Node X="1" Y="2" Z="42" Value="-0.2504082" />
        		<Node X="2" Y="2" Z="42" Value="-0.2743937" />
        		<Node X="0" Y="0" Z="43" Value="0.1132936" />
        		<Node X="1" Y="0" Z="43" Value="-1.633733" />
        		<Node X="2" Y="0" Z="43" Value="0.5591072" />
        		<Node X="0" Y="1" Z="43" Value="0.7104746" />
        		<Node X="1" Y="1" Z="43" Value="1.830815" />
        		<Node X="2" Y="1" Z="43" Value="1.436787" />
        		<Node X="0" Y="2" Z="43" Value="-0.1145731" />
        		<Node X="1" Y="2" Z="43" Value="0.1250063" />
        		<Node X="2" Y="2" Z="43" Value="-0.157924" />
        		<Node X="0" Y="0" Z="44" Value="-0.349147" />
        		<Node X="1" Y="0" Z="44" Value="0.3923524" />
        		<Node X="2" Y="0" Z="44" Value="-0.2887461" />
        		<Node X="0" Y="1" Z="44" Value="0.1901588" />
        		<Node X="1" Y="1" Z="44" Value="1.04338" />
        		<Node X="2" Y="1" Z="44" Value="1.554292" />
        		<Node X="0" Y="2" Z="44" Value="0.01251187" />
        		<Node X="1" Y="2" Z="44" Value="-0.07875831" />
        		<Node X="2" Y="2" Z="44" Value="-0.3525737" />
        		<Node X="0" Y="0" Z="45" Value="0.2201274" />
        		<Node X="1" Y="0" Z="45" Value="-2.493914" />
        		<Node X="2" Y="0" Z="45" Value="0.7733946" />
        		<Node X="0" Y="1" Z="45" Value="-0.8519823" />
        		<Node X="1" Y="1" Z="45" Value="1.001191" />
        		<Node X="2" Y="1" Z="45" Value="2.241728" />
        		<Node X="0" Y="2" Z="45" Value="0.03651591" />
        		<Node X="1" Y="2" Z="45" Value="0.4484932" />
        		<Node X="2" Y="2" Z="45" Value="-0.06920049" />
        		<Node X="0" Y="0" Z="46" Value="-0.936515" />
        		<Node X="1" Y="0" Z="46" Value="-1.173076" />
        		<Node X="2" Y="0" Z="46" Value="1.238834" />
        		<Node X="0" Y="1" Z="46" Value="0.9181442" />
        		<Node X="1" Y="1" Z="46" Value="1.752505" />
        		<Node X="2" Y="1" Z="46" Value="0.5683882" />
        		<Node X="0" Y="2" Z="46" Value="-0.07035258" />
        		<Node X="1" Y="2" Z="46" Value="0.03659626" />
        		<Node X="2" Y="2" Z="46" Value="-0.02968399" />
        		<Node X="0" Y="0" Z="47" Value="0.1427311" />
        		<Node X="1" Y="0" Z="47" Value="-3.099199" />
        		<Node X="2" Y="0" Z="47" Value="-0.9049471" />
        		<Node X="0" Y="1" Z="47" Value="0.771832" />
        		<Node X="1" Y="1" Z="47" Value="1.965032" />
        		<Node X="2" Y="1" Z="47" Value="1.828468" />
        		<Node X="0" Y="2" Z="47" Value="-0.1411418" />
        		<Node X="1" Y="2" Z="47" Value="0.2229437" />
        		<Node X="2" Y="2" Z="47" Value="0.1171091" />
        		<Node X="0" Y="0" Z="48" Value="0.1909064" />
        		<Node X="1" Y="0" Z="48" Value="0.5024482" />
        		<Node X="2" Y="0" Z="48" Value="1.095386" />
        		<Node X="0" Y="1" Z="48" Value="0.3759831" />
        		<Node X="1" Y="1" Z="48" Value="1.345439" />
        		<Node X="2" Y="1" Z="48" Value="0.6294759" />
        		<Node X="0" Y="2" Z="48" Value="-0.02446398" />
        		<Node X="1" Y="2" Z="48" Value="-0.193266" />
        		<Node X="2" Y="2" Z="48" Value="-0.2045425" />
        		<Node X="0" Y="0" Z="49" Value="0.7162808" />
        		<Node X="1" Y="0" Z="49" Value="-2.214506" />
        		<Node X="2" Y="0" Z="49" Value="0.8649447" />
        		<Node X="0" Y="1" Z="49" Value="1.871275" />
        		<Node X="1" Y="1" Z="49" Value="2.490769" />
        		<Node X="2" Y="1" Z="49" Value="1.605241" />
        		<Node X="0" Y="2" Z="49" Value="-0.2157702" />
        		<Node X="1" Y="2" Z="49" Value="0.0398576" />
        		<Node X="2" Y="2" Z="49" Value="-0.30811" />
        		<Node X="0" Y="0" Z="50" Value="0.538143" />
        		<Node X="1" Y="0" Z="50" Value="-0.8824145" />
        		<Node X="2" Y="0" Z="50" Value="0.01733304" />
        		<Node X="0" Y="1" Z="50" Value="0.04796191" />
        		<Node X="1" Y="1" Z="50" Value="2.129442" />
        		<Node X="2" Y="1" Z="50" Value="2.682483" />
        		<Node X="0" Y="2" Z="50" Value="-0.02275831" />
        		<Node X="1" Y="2" Z="50" Value="-0.329757" />
        		<Node X="2" Y="2" Z="50" Value="-0.4441737" />
        		<Node X="0" Y="0" Z="51" Value="-0.07612614" />
        		<Node X="1" Y="0" Z="51" Value="-2.40694" />
        		<Node X="2" Y="0" Z="51" Value="0.03193626" />
        		<Node X="0" Y="1" Z="51" Value="-0.2932324" />
        		<Node X="1" Y="1" Z="51" Value="2.623614" />
        		<Node X="2" Y="1" Z="51" Value="1.631239" />
        		<Node X="0" Y="2" Z="51" Value="0.0364047" />
        		<Node X="1" Y="2" Z="51" Value="0.1970877" />
        		<Node X="2" Y="2" Z="51" Value="-0.1242779" />
        		<Node X="0" Y="0" Z="52" Value="-0.833669" />
        		<Node X="1" Y="0" Z="52" Value="-1.254515" />
        		<Node X="2" Y="0" Z="52" Value="-0.168173" />
        		<Node X="0" Y="1" Z="52" Value="-2.982485" />
        		<Node X="1" Y="1" Z="52" Value="3.099726" />
        		<Node X="2" Y="1" Z="52" Value="2.312814" />
        		<Node X="0" Y="2" Z="52" Value="0.2808829" />
        		<Node X="1" Y="2" Z="52" Value="0.2039993" />
        		<Node X="2" Y="2" Z="52" Value="-0.0898677" />
        		<Node X="0" Y="0" Z="53" Value="-0.3158733" />
        		<Node X="1" Y="0" Z="53" Value="-2.156559" />
        		<Node X="2" Y="0" Z="53" Value="2.417242" />
        		<Node X="0" Y="1" Z="53" Value="-1.047516" />
        		<Node X="1" Y="1" Z="53" Value="3.627437" />
        		<Node X="2" Y="1" Z="53" Value="1.944811" />
        		<Node X="0" Y="2" Z="53" Value="0.09728091" />
        		<Node X="1" Y="2" Z="53" Value="0.1532321" />
        		<Node X="2" Y="2" Z="53" Value="-0.6192255" />
        		<Node X="0" Y="0" Z="54" Value="-0.04899749" />
        		<Node X="1" Y="0" Z="54" Value="2.848426" />
        		<Node X="2" Y="0" Z="54" Value="0.2904806" />
        		<Node X="0" Y="1" Z="54" Value="-2.252651" />
        		<Node X="1" Y="1" Z="54" Value="2.962822" />
        		<Node X="2" Y="1" Z="54" Value="3.871899" />
        		<Node X="0" Y="2" Z="54" Value="0.1288705" />
        		<Node X="1" Y="2" Z="54" Value="-0.09419243" />
        		<Node X="2" Y="2" Z="54" Value="-0.1377179" />
        		<Node X="0" Y="0" Z="55" Value="0.8474329" />
        		<Node X="1" Y="0" Z="55" Value="1.214333" />
        		<Node X="2" Y="0" Z="55" Value="-0.52802" />
        		<Node X="0" Y="1" Z="55" Value="-0.4807324" />
        		<Node X="1" Y="1" Z="55" Value="4.788553" />
        		<Node X="2" Y="1" Z="55" Value="0.5269803" />
        		<Node X="0" Y="2" Z="55" Value="-0.134818" />
        		<Node X="1" Y="2" Z="55" Value="-0.2000996" />
        		<Node X="2" Y="2" Z="55" Value="0.07953535" />
        		<Node X="0" Y="0" Z="56" Value="0.1961866" />
        		<Node X="1" Y="0" Z="56" Value="0.630663" />
        		<Node X="2" Y="0" Z="56" Value="-1.200837" />
        		<Node X="0" Y="1" Z="56" Value="-1.504695" />
        		<Node X="1" Y="1" Z="56" Value="4.681966" />
        		<Node X="2" Y="1" Z="56" Value="3.99545" />
        		<Node X="0" Y="2" Z="56" Value="0.05390552" />
        		<Node X="1" Y="2" Z="56" Value="-0.2746132" />
        		<Node X="2" Y="2" Z="56" Value="0.09590138" />
        		<Node X="0" Y="0" Z="57" Value="-0.192025" />
        		<Node X="1" Y="0" Z="57" Value="2.120564" />
        		<Node X="2" Y="0" Z="57" Value="-0.5196728" />
        		<Node X="0" Y="1" Z="57" Value="-2.184315" />
        		<Node X="1" Y="1" Z="57" Value="3.931082" />
        		<Node X="2" Y="1" Z="57" Value="4.095085" />
        		<Node X="0" Y="2" Z="57" Value="0.1436728" />
        		<Node X="1" Y="2" Z="57" Value="-0.6218677" />
        		<Node X="2" Y="2" Z="57" Value="0.02701958" />
        		<Node X="0" Y="0" Z="58" Value="0.6309627" />
        		<Node X="1" Y="0" Z="58" Value="-0.869297" />
        		<Node X="2" Y="0" Z="58" Value="0.2767608" />
        		<Node X="0" Y="1" Z="58" Value="1.617473" />
        		<Node X="1" Y="1" Z="58" Value="5.58949" />
        		<Node X="2" Y="1" Z="58" Value="6.701704" />
        		<Node X="0" Y="2" Z="58" Value="-0.2136974" />
        		<Node X="1" Y="2" Z="58" Value="-0.151066" />
        		<Node X="2" Y="2" Z="58" Value="-0.08292479" />
        		<Node X="0" Y="0" Z="59" Value="-0.1033018" />
        		<Node X="1" Y="0" Z="59" Value="-0.8923529" />
        		<Node X="2" Y="0" Z="59" Value="1.542079" />
        		<Node X="0" Y="1" Z="59" Value="-0.8160006" />
        		<Node X="1" Y="1" Z="59" Value="3.976453" />
        		<Node X="2" Y="1" Z="59" Value="7.305612" />
        		<Node X="0" Y="2" Z="59" Value="0.0611175" />
        		<Node X="1" Y="2" Z="59" Value="-0.1232658" />
        		<Node X="2" Y="2" Z="59" Value="-0.6120446" />
    """
    grid_movement_x1 = []
    for line in nodedatatest.strip().split("\n"):
        start = line.find('Value="') + len('Value="')
        end = line.find('"', start)
        value = line[start:end]
        grid_movement_x1.append(value)
    grid_movement_x1 = np.asarray(grid_movement_x1)
    assert not np.array_equal(get_data_from_warp_xml(xml_file_path, "GridMovementX", 2), grid_movement_x1)

    # level 1, negative floats
    axisY_negative = [
    -95.60207, -110.2457, -89.65818, -122.977, -75.29381, -145.2447, -88.36815,
    -134.5136, -79.06438, -144.8848, -80.94444, -148.9504, -98.82204, -131.589,
    -99.3392, -134.0308, -108.0799, -132.8979, -102.9604, -109.8975, -123.7455,
    -156.5575, -71.82225, -128.3785, -141.1216, -111.4745, -105.5518, -107.1509,
    -141.7749, 0, -88.65258, 52.32646, -125.3249, 7.120238, -62.03314, -51.76203,
    -64.6597, -33.80381, -44.38956, -33.72198, -69.23692, 9.592659, -64.28349,
    -26.47904, -21.23565, -0.4442041, -37.51812, 10.85751, -52.15116, 23.32489,
    -40.59274, 20.9565, -7.281012, 32.14969, -19.47281, 54.45569, -12.57366,
    46.69533, -21.36308, 59.44625]
    axisY_negative = np.asarray(axisY_negative)
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "AxisOffsetY", 1), axisY_negative)

    # level 3, must raise Value Error exception
    with pytest.raises(ValueError):
        get_data_from_warp_xml(xml_file_path, "AxisOffsetY", 3)

    # level1/2 with absent node_name
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "Absent", 2), None)


    # Level 1 on something that has children, what happens?this function doesn't really handle this possibility
    #get_data_from_warp_xml(xml_file_path, "GridCTF", 1)

    #level 1, strings, (paths) -- fails!
    # Level 1, booleans -- fails because reads 'True' as string but should be interpreted as boolean!
    """
    moviepath = np.array["017_01.mrc","017_02.mrc","017_03.mrc","017_04.mrc","017_05.mrc","017_06.mrc",
    "017_07.mrc","017_08.mrc","017_09.mrc","017_10.mrc","017_11.mrc","017_12.mrc",
    "017_13.mrc","017_14.mrc","017_15.mrc","017_16.mrc","017_17.mrc","017_18.mrc",
    "017_19.mrc","017_20.mrc","017_21.mrc","017_22.mrc","017_23.mrc","017_24.mrc",
    "017_25.mrc","017_26.mrc","017_27.mrc","017_28.mrc","017_29.mrc","017_30.mrc",
    "017_31.mrc","017_32.mrc","017_33.mrc","017_34.mrc","017_35.mrc","017_36.mrc",
    "017_37.mrc","017_38.mrc","017_39.mrc","017_40.mrc","017_41.mrc","017_42.mrc",
    "017_43.mrc","017_44.mrc","017_45.mrc","017_46.mrc","017_47.mrc","017_48.mrc",
    "017_49.mrc","017_50.mrc","017_51.mrc","017_52.mrc","017_53.mrc","017_54.mrc",
    "017_55.mrc","017_56.mrc","017_57.mrc","017_58.mrc","017_59.mrc","017_60.mrc"]
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "MoviePath", 1), moviepath)
    
    usetilt = np.array([ True,  True,  True,  True,  True,  True,  True,  True,  True,
       True,  True,  True,  True,  True,  True,  True,  True,  True,
       True,  True,  True,  True,  True,  True,  True,  True,  True,
       True,  True,  True,  True,  True,  True,  True,  True,  True,
       True,  True,  True,  True,  True,  True,  True,  True,  True,
       True,  True,  True,  True,  True,  True,  True,  True,  True,
       True,  True,  True,  True,  True,  True,  True,  True,  True])
    assert np.array_equal(get_data_from_warp_xml(xml_file_path, "UseTilt", 1), usetilt)

    """

#Add exception for missing columns?
#Add exceptions?
def test_warp_ctf_read():
    current_dir = Path(__file__).parent
    xml_file_path = str(current_dir / "test_data" / "TS_018" / "018.xml")
    gridctf  = [
    3.409815, 3.398723, 3.389318, 3.392323, 3.424242, 3.371011, 3.403402, 3.406947, 3.42302, 3.378743,
    3.392365, 3.390212, 3.419454, 3.38763, 3.404047, 3.388702, 3.404345, 3.378603, 3.388518, 3.382968,
    3.370579, 3.384403, 3.392067, 3.387562, 3.397726, 3.391282, 3.387162, 3.37812, 3.374513, 3.382992,
    3.383263, 3.376348, 3.385212, 3.385358, 3.367899, 3.360602, 3.350081, 3.362278, 3.352579, 3.345044,
    3.331407, 3.356446, 3.34499, 3.327942, 3.324675, 3.344646, 3.350497, 3.312646, 3.308363, 3.295593,
    3.296385, 3.273645, 3.300465, 3.2972, 3.288325, 3.248272, 3.270276, 3.309069, 3.392386, 3.353555]
    gridctf = np.asarray(gridctf, dtype=float)


    gridctf_da = [
    164, 164, 164, 164, 164, 164, 164, 164, 164, 164,
    164, 164, 164, 164, 164, 164, 164, 164, 164, 164,
    164, 164, 164, 164, 164, 164, 164, 164, 164, 164,
    164, 164, 164, 164, 164, 164, 164, 164, 164, 164,
    164, 164, 164, 164, 164, 164, 164, 164, 164, 164,
    164, 164, 164, 164, 164, 164, 164, 164, 164, 164]
    gridctf_da = np.asarray(gridctf_da, dtype=float)


    gridctf_phase = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    gridctf_phase = np.asarray(gridctf_phase, dtype=float)

    test_columns = ["defocus1", "defocus2", "astigmatism", "phase_shift", "defocus_mean"]
    test_df = pd.DataFrame(columns=test_columns)
    test_df["defocus_mean"] = test_df["defocus1"] = test_df["defocus2"] = gridctf
    test_df["astigmatism"] = gridctf_da
    test_df["phase_shift"] = gridctf_phase

    pd.testing.assert_frame_equal(test_df, warp_ctf_read(xml_file_path))

