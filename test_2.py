import zlib
import sys

import json

# Convert a Python object to a JSON string
data = {
    "name": "John Doe",
    "age": 30,
    "message":  'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque nisl eros,'\
'pulvinar facilisis justo mollis, auctor consequat urna. Morbi a bibendum metus. '\
'Donec scelerisque sollicitudin enim eu venenatis. Duis tincidunt laoreet ex, '\
'in pretium orci vestibulum eget. Class aptent taciti sociosqu ad litora torquent'\
'per conubia nostra, per inceptos himenaeos. Duis pharetra luctus lacus ut '\
'vestibulum. Maecenas ipsum lacus, lacinia quis posuere ut, pulvinar vitae dolor.'\
'Integer eu nibh at nisi ullamcorper sagittis id vel leo. Integer feugiat '\
'faucibus libero, at maximus nisl suscipit posuere. Morbi nec enim nunc. '\
'Phasellus bibendum turpis ut ipsum egestas, sed sollicitudin elit convallis. '\
'Cras pharetra mi tristique sapien vestibulum lobortis. Nam eget bibendum metus, '\
'non dictum mauris. Nulla at tellus sagittis, viverra est a, bibendum metus.', 
    "email": "john.doe@example.com",
    "ref": {
      "ita": {
        "name": "italo"
      },
      "eng": "paolo"
    }
}


def zip_string(input_string):
    compressed = zlib.compress(input_string.encode())
    return compressed

def unzip_string(compressed_string):
    decompressed = zlib.decompress(compressed_string).decode()
    return decompressed







text = json.dumps(data)
compressed = zip_string(text)
decompressed = unzip_string(compressed)


# Convert a JSON string to a Python object


print(data, sys.getsizeof(data))
print('_________')
print(text, sys.getsizeof(text))
print('--------')
print(compressed, sys.getsizeof(compressed))
print('--------')
print(decompressed, sys.getsizeof(decompressed))
data = json.loads(decompressed)
print(data, sys.getsizeof(data))