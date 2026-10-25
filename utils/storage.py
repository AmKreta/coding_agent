byte = 1
kilo_byte = 1024*byte
mega_byte = 1024*byte
giga_byte = 1024*mega_byte


def byte_to_mega_byte(byte: int) -> int:
    return byte/mega_byte