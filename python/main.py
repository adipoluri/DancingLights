from python import led
from python.audio import startStream
from python.signalprocessing import microphone_update


def main():
    print("Started Script")
    # TODO: Need to implement data transfer over wifi
    led.update()
    startStream(microphone_update)


main()
