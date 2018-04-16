import piggyphoto, pygame
import os
import time
import RPi.GPIO as GPIO
import subprocess

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    return False

def show(file):
    picture = pygame.image.load(file)

    main_surface.blit(picture, (0, 0))
    pygame.display.flip()

C = piggyphoto.camera()
C.leave_locked()
C.capture_preview('preview.jpg')

picture = pygame.image.load("preview.jpg")
pygame.display.set_mode(picture.get_size())
main_surface = pygame.display.get_surface()

while not quit_pressed():
    C.capture_preview('preview.jpg')
    show("preview.jpg")
    if (GPIO.input(18) == False):
        print('Button Pressed')
        time.sleep(0.5)
        #C.capture_image('snap.jpg')
        subprocess.call('gphoto2 ' +
                    '--capture-image-and-download ' +
                    '--filename="snap.jpg" ',
                    shell=True)
        show('snap.jpg')
    