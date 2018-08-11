import base64
import argparse
parser = argparse.ArgumentParser()


def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


if __name__ == '__main__':
    parser.add_argument(
        'mode', choices=['e', 'd'], help='e: encode, d: decode')
    parser.add_argument('key', help='secrete key')
    parser.add_argument('text', help='encrypted or clear text')
    args = parser.parse_args()
    if args.mode == 'e':
        print(encode(args.key, args.text))
    else:
        print(decode(args.key, args.text))
