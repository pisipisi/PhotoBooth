#!/usr/bin/python
from uuid import uuid4
import time, os, io, subprocess, Image, shutil, cups, sys, pygame
import RPi.GPIO as GPIO
from os.path import join, basename, expanduser
from pygame.locals import *
# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
PRINT_LED = 22
POSE_LED = 24
BUTTON_LED = 23
GPIO.setup(POSE_LED, GPIO.OUT)
GPIO.setup(BUTTON_LED, GPIO.OUT)
GPIO.setup(PRINT_LED, GPIO.OUT)
GPIO.output(BUTTON_LED, True)
GPIO.output(PRINT_LED, False)


bounceMillis = 800 #waits 800 ms before noticing another button press
FPS = 25
#               R    G    B    A
WHITE       = (255, 255, 255, 255)
GRAY        = (185, 185, 185, 255)
BLACK       = (  0,   0,   0, 255)
DARKBLUE    = (  0,   0, 100, 255)
TEXTSHADOWCOLOR = GRAY
TEXTCOLOR = WHITE
BGCOLOR = DARKBLUE

# printout size
print_2x6 = False
print_2up = False
print_width = 2 if print_2x6 else 6 #inches
print_height = 6 if print_2x6 else 4 #inches
print_w_dpi = 330
print_h_dpi = 330
print_size = (print_width * print_w_dpi, print_height * print_h_dpi)

blank_thumb = (20,20,20,255)

#printer
printer_name = "Canon_CP710"
printer_copies = 1

# layout - each "grid" is 8x8px at 640x480
grid_width = 80
grid_height = 60

# photo preview in grid units
preview_pad    = 1
preview_x      = 4
preview_y      = 14
preview_width  = 48
preview_height = 40

# thumb strip in grid units
thumb_strip_pad    = 1
thumb_strip_x      = 54
thumb_strip_y      = 0
thumb_strip_width  = 20
thumb_strip_height = grid_height
thumb_photo_width  = thumb_strip_width - 2 * thumb_strip_pad
thumb_photo_height = thumb_photo_width * 3 / 4

# font sizes in grid units
basic_font_size    = 4
big_font_size      = 8
huge_font_size     = 50

thumb_size = (400,300)
thumb_time = 2
thumb_last_sw = 0
thumb_index = 1
thumb_loc = '/home/pi/scripts/photobooth/photos_thumb/'
thumb_strip = []

# Where to spit out our qrcode, watermarked image, and local html
out = expanduser('/home/pi/scripts/photobooth/sxsw')

# The watermark to apply to all images
watermark_img = expanduser('/home/pi/scripts/fedora.png')

# The camera configuration
# Use gphoto2 --list-config and --get-config for more information
gphoto_config = {
    '/main/imgsettings/imagesize': 3, # small
    '/main/imgsettings/imagequality': 0, # normal
    '/main/capturesettings/zoom': 70, # zoom factor
}
#get_preview_command = "gphoto2 --capture-preview --filename /home/pi/scripts/photobooth/preview.jpg --force-overwrite"



def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BIGFONT, HUGEFONT, WINDOWWIDTH, WINDOWHEIGHT, CAMERA, GRID_W_PX, GRID_H_PX
    setupDisplay()
    pygame.init()
    WINDOWWIDTH = pygame.display.Info().current_w
    GRID_W_PX   = int(WINDOWWIDTH / grid_width)
    WINDOWHEIGHT = pygame.display.Info().current_h
    GRID_H_PX    = int(WINDOWHEIGHT / grid_height)
    FPSCLOCK = pygame.time.Clock()
    pygame.mouse.set_visible(False) #hide the mouse cursor
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), pygame.FULLSCREEN, 32)
    BASICFONT = pygame.font.Font('freesansbold.ttf', int(GRID_H_PX * basic_font_size))
    BIGFONT = pygame.font.Font('freesansbold.ttf', int(GRID_H_PX * big_font_size))
    HUGEFONT = pygame.font.Font('freesansbold.ttf', int(GRID_H_PX * huge_font_size))
    pygame.display.set_caption('Photobooth')
    
    showTextScreen('Photobooth','Loading...')
    
    loadThumbs()
    pygame.event.clear() 
    try:          
        while True:
        
            #if (GPIO.input(18) == False):
            #    print('Button Pressed')
            #    time.sleep(0.5)
            
             #   photoShoot()
            #    print("please wait while your photos print...")
            #    subprocess.call("rm /home/pi/scripts/photobooth/sxsw/*.jpg", shell= True)
                # TODO: implement a reboot button
                # Wait to ensure that print queue doesn't pile up
                # TODO: check status of printer instead of using this arbitrary wait time
            #    time.sleep(10)
             #   print("ready for next round")
            #    GPIO.output(PRINT_LED, False)
             #   GPIO.output(BUTTON_LED, True)
    
         # Turn off program 
         #   PRESSTIME = 0
         #   for j in range(30):                     #start counting
         #       if ( GPIO.input(18) == False):   #if it is still being pressed
         #           print "pressed and released"      #print something
         #           PRESSTIME = PRESSTIME + 1                     # add something to J
          #          if ( PRESSTIME >= 25 ):                        # if you have been pressing for 28*0.1=2.8 seconds then
         #               #os.system("stop")            # stop program the music
         #               print "stop program"
         #               terminate()
          #              time.sleep(0.1) 
        # wait 0.1sec, then loop again to see if you are holding the PLAYBUTTON still
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    GPIO.output(BUTTON_LED, False)
                    if event.key == K_ESCAPE:
                        pygame.event.clear()
                        powerOff() # terminate if the KEYUP event was for the Esc key
                    elif event.key == K_SPACE:
                        pygame.event.clear()
                        photoShoot()
                        pygame.event.clear()
                    elif event.key == K_e:
                        pygame.event.clear()
                        terminate()
            idleScreen()
        #DrawPreview()   
    except:
        GPIO.cleanup()
        print "EXCEPTION"
        
def buttonPress(channel): 
    if (GPIO.input(18) == False):
        print('Button Pressed')
        time.sleep(0.5)
            
        photoShoot()
        print("please wait while your photos print...")
        subprocess.call("rm /home/pi/scripts/photobooth/sxsw/*.jpg", shell= True)
    # TODO: implement a reboot button
    # Wait to ensure that print queue doesn't pile up
    # TODO: check status of printer instead of using this arbitrary wait time
        time.sleep(5)
        print("ready for next round")
        GPIO.output(PRINT_LED, False)
        GPIO.output(BUTTON_LED, True)
                
                
def setupDisplay():
    disp_no = os.getenv("DISPLAY")
    if disp_no:
        print "I'm running under X display = {0}".format(disp_no)
    
    # Check which frame buffer drivers are available
    # Start with fbcon since directfb hangs with composite output
    drivers = ['fbcon', 'directfb', 'svgalib']
    found = False
    for driver in drivers:
        # Make sure that SDL_VIDEODRIVER is set
        if not os.getenv('SDL_VIDEODRIVER'):
            os.putenv('SDL_VIDEODRIVER', driver)
        try:
            pygame.display.init()
        except pygame.error:
            print 'Driver: {0} failed.'.format(driver)
            continue
        found = True
        break

    if not found:
        raise Exception('No suitable video driver found!')    

def processPhoto(photos):
    save_name = str(time.time())
    montage = Image.new('RGBA',print_size,WHITE)
    paste_x = 0
    paste_y = 0
    first = 0
    bg = Image.open("/home/pi/scripts/photobooth/bg.jpg")
    montage.paste(bg,(0,0))
    if print_2x6 :
        for photo in photos:
            photo_w = print_size[0]
            photo_h = int(photo_w * (photo.size[1] / photo.size[0]))
            resized = photo.resize((photo_w,photo_h),Image.ANTIALIAS)
            montage.paste(resized,(0,paste_y))
            paste_y += photo_h
    else:
        for photo in photos:
            #photo.save('/home/pi/scripts/photobooth/raw_images/'+save_name+'-'+str(paste_x)+str(paste_y)+'.jpg','JPEG',quality=80)
            if first == 0:
                photo_h = int((print_size[1]-80)*2/3 - 30)
                photo_w = int((print_size[0]-80)*2/3 - 30)
                first=first+1
            else:
                photo_h = int(((print_size[1]-80)*2/3 - 30)/2 - 15)
                photo_w = int(((print_size[0]-80)*2/3 - 30)/2 - 15)
            resized = photo.resize((photo_w,photo_h),Image.ANTIALIAS)
            montage.paste(resized,(paste_x+15,paste_y+15))
            if paste_x == 0 and paste_y == 0 :
                print "second pic"
                paste_y = photo_h + 30
                paste_x = 10
            else :
                paste_x = photo_w + 30
                print "third pic"
        logo = Image.open("/home/pi/scripts/photobooth/wedding.jpg")
        basewidth = int(print_size[0] - (print_size[0]-80)*2/3 - 30)
        wpercent = (basewidth/float(logo.size[0]))
        hsize = int((float(logo.size[1])*float(wpercent)))
        logo = logo.resize((basewidth,hsize), Image.ANTIALIAS)
        montage.paste(logo,(print_size[0] - basewidth - 15,15))
    montage.save("/home/pi/scripts/photobooth/print_image.jpg","JPEG",quality=100)
    shutil.copyfile("/home/pi/scripts/photobooth/print_image.jpg","/home/pi/scripts/photobooth/montages/" + str(time.time()) + ".jpg")
    
def printPhoto(photo,photos):
    printer_conn = cups.Connection()
    #################################################################################
    printer_conn.printFile(printer_name, photo, "PhotoBooth",{"copies": str(printer_copies)})
    displayImage(photo)
    time.sleep(10)
    updateThumb(photos[0])
    showTextScreen('Printing',str(printer_copies) + ' copies')
    time.sleep(5)
    
def displayImage(image):
    image = pygame.transform.scale(pygame.image.load(image),(WINDOWWIDTH,WINDOWHEIGHT))
    DISPLAYSURF.blit(image,(0,0))
    pygame.display.update()
       
def capturePhoto():
    """ Capture a photo and download it from the camera """
    filename = join(out, '%s.jpg' % str(uuid4()))
    cfg = ['--set-config=%s=%s' % (k, v) for k, v in gphoto_config.items()]
    subprocess.call('gphoto2 ' +
                    '--capture-image-and-download ' +
                    '--filename="%s" ' % filename,
                    shell=True)
    byteImgIO = io.BytesIO()
    byteImg = Image.open(filename)
    byteImg.save(byteImgIO, "JPEG")
    byteImgIO.seek(0)
    byteImg = byteImgIO.read()
    # Non test code
    dataBytesIO = io.BytesIO(byteImg)
    photo = Image.open(dataBytesIO)
    img = pygame.image.load(filename)
    displayImage(filename)
    time.sleep(0.7)
    return photo 
 
def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect() 

def idleScreen():
    global thumb_last_sw
    #get_preview_command = "gphoto2 --capture-preview --filename /home/pi/scripts/photobooth/preview.jpg --force-overwrite"
    #p = subprocess.Popen(get_preview_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    #p.wait()#must wait until the image returns or the images never get fully loaded
    
    #image = pygame.image.load("/home/pi/scripts/photobooth/preview.jpg").convert_alpha()
    #image =  pygame.transform.scale(image, (GRID_W_PX * (preview_width - (2 * preview_pad)),GRID_H_PX * (preview_height - (2 * preview_pad))))
    DISPLAYSURF.fill(BGCOLOR)
    
    #GRID_W_PX * (preview_width - (2 * preview_pad)),GRID_H_PX * (preview_height - (2 * preview_pad))
    
    border = pygame.Surface((GRID_W_PX * preview_width, GRID_H_PX * preview_height))
    border.fill(BLACK)
    borderRect = DISPLAYSURF.blit(border,(GRID_W_PX * preview_x, GRID_H_PX * preview_y))
    #borderRect = DISPLAYSURF.blit(image,(GRID_W_PX * preview_x, GRID_H_PX * preview_y))
    startSurf, startRect = makeTextObjs('Press Start', BASICFONT, WHITE)
    startRect.midbottom = (borderRect[2]/2+borderRect[0],borderRect[3]+borderRect[1]-10)
    DISPLAYSURF.blit(startSurf, startRect)
    titleSurf, titleRect = makeTextObjs('Nau Photobooth', BIGFONT, GRAY)
    titleRect.bottomleft = (borderRect[0] + preview_pad * GRID_W_PX ,borderRect[1])
    DISPLAYSURF.blit(titleSurf, titleRect)

    pygame.display.update()
    
    thumb_last_sw = 0
    while not GPIO.input(18) == False:
        pygame.display.update(filmStrip())
        FPSCLOCK.tick(FPS) 
       
def filmStrip():
    global thumb_index, thumb_last_sw
    if time.time() - thumb_time> thumb_last_sw:
        thumb_last_sw = time.time()
        strip = pygame.Surface((thumb_strip_width * GRID_W_PX, thumb_strip_height * GRID_H_PX),pygame.SRCALPHA)
        strip.fill(BLACK)
        thumb_h_pos = (thumb_photo_height + thumb_strip_pad) * GRID_H_PX
        thumb_index += 1
        for i in range (0,8):
            strip.blit(thumb_strip[i],(thumb_strip_pad * GRID_W_PX,((thumb_index+i)%8)*thumb_h_pos))
        return DISPLAYSURF.blit(strip,(GRID_W_PX * thumb_strip_x, GRID_H_PX * thumb_strip_y))
          
def photoShoot():
    images = []
    
    readySurf, readyRect = makeTextObjs('Get Ready', BIGFONT, WHITE)
    readyRect.midbottom = (WINDOWWIDTH/2,WINDOWHEIGHT/10*9)
    DISPLAYSURF.blit(readySurf, readyRect)
    pygame.display.update()
    time.sleep(1)
    
    for photo in range (0,3):
        time.sleep(0.1)
        # Count down loop, shows big numbers on the screen
        for i in range (5,0,-1):
            DISPLAYSURF.fill(BLACK)
            numSurf, numRect = makeTextObjs(str(i), HUGEFONT, WHITE)
            numRect.center = (WINDOWWIDTH/2,WINDOWHEIGHT/2- GRID_H_PX)
            DISPLAYSURF.blit(numSurf, numRect)
            numphotosSurf, numphotosRect = makeTextObjs('Taking Photo ' + str(photo+1) + ' of ' + str(3),BIGFONT,WHITE)
            numphotosRect.midbottom = (WINDOWWIDTH / 2, WINDOWHEIGHT - GRID_H_PX * 4)
            DISPLAYSURF.blit(numphotosSurf, numphotosRect)
            pygame.display.update()
            time.sleep(0.7) # each number shows for this amount of time
        # Clear the Screen

        print("pose!")
        showTextScreen('POSE!!!','Taking Photo ' + str(photo+1)) 
        GPIO.output(BUTTON_LED, False)
        GPIO.output(POSE_LED, True)
        time.sleep(0.5)
        DISPLAYSURF.fill(BLACK)
        #takephotoSurf, takephotoRect = makeTextObjs('Taking Photo ' + str(photo+1),BIGFONT,WHITE)
        #takephotoRect.midbottom = (WINDOWWIDTH/2,WINDOWHEIGHT/10*9)
        #DISPLAYSURF.blit(takephotoSurf, takephotoRect) 
        pygame.display.update()
        """
        for i in range(5):
            GPIO.output(POSE_LED, False)
            time.sleep(0.4)
            GPIO.output(POSE_LED, True)
            time.sleep(0.4)
        for i in range(5):
            GPIO.output(POSE_LED, False)
            time.sleep(0.1)
            GPIO.output(POSE_LED, True)
            time.sleep(0.1)
        """
        GPIO.output(POSE_LED, False)
        print("SNAP") 
        #showTextScreen('Processing!!!','Photo ' + str(photo+1)) 
        images.append(capturePhoto())  
        time.sleep(0.5)
        
    DISPLAYSURF.fill(BLACK) # clear the screen
    pygame.display.update()
    showTextScreen('Photobooth','Processing...')    
    print("please wait while process your photos...")
    processPhoto(images) 
    GPIO.output(PRINT_LED, True)
    printPhoto('/home/pi/scripts/photobooth/print_image.jpg',images)
    
def updateThumb(image):
    global thumb_strip
    thumb_size = (int(thumb_photo_width * GRID_W_PX), int(thumb_photo_height * GRID_H_PX))
    for i in range (7,0,-1):
        try:
            thumb_strip[i] = thumb_strip[i - 1]
        except:
            thumb_strip[i] = pygame.Surface(thumb_size)
            thumb_strip[i].fill(blank_thumb)
        try:
            os.rename(thumb_loc+str(i)+'.jpg',thumb_loc+str(i+1)+'.jpg')
        except:
            continue
    image.save(thumb_loc+str(1)+'.jpg')
#    photo_edit = pgmagick.Image(image)
#    photo_edit.quality(100)
#    photo_edit.scale(str(thumb_size[0])+'x'+str(thumb_size[1]))
#    photo_edit.write(thumb_loc+'1.jpg')
    thumb_strip[0] = pygame.image.load(thumb_loc+str(1)+'.jpg').convert()
    thumb_strip[0] = pygame.transform.smoothscale(thumb_strip[0],thumb_size)

def terminate():
    GPIO.cleanup()
    pygame.quit()
    sys.exit()  
      
def loadThumbs():
    global thumb_strip
    thumb_size = (int(thumb_photo_width * GRID_W_PX), int(thumb_photo_height * GRID_H_PX))
    for i in range (0,8):
        try:
            thumb_strip.append(pygame.image.load(thumb_loc+str(i+1)+'.jpg').convert())
            thumb_strip[i] = pygame.transform.smoothscale(thumb_strip[i],thumb_size)
        except:
            thumb_strip.append(pygame.Surface(thumb_size))
            thumb_strip[i].fill(blank_thumb)   
             
def showTextScreen(text, text2):
    # This function displays large text in the
    DISPLAYSURF.fill(BLACK)
    
    # Draw the text drop shadow
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTSHADOWCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the text
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTCOLOR)
    titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Draw the additional "Press a key to play." text.
    pressKeySurf, pressKeyRect = makeTextObjs(text2, BASICFONT, TEXTCOLOR)
    pressKeyRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    pygame.display.update()
      
def DrawPreview():
    # draws the preview image from the camera onto the screen
    global last_preview
    DISPLAYSURF.fill(BGCOLOR)
    p = subprocess.Popen(get_preview_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    
    p.wait()#must wait until the image returns or the images never get fully loaded
    
    image = pygame.image.load("preview.jpg").convert_alpha()

    #position lower right preview image
    DISPLAYSURF.blit(image,((width-320),(height - 240)))
    
    pygame.display.update()
    #stores last to make transitions look less choppy    
    last_preview = image 
    
GPIO.add_event_detect(18,GPIO.RISING,callback=buttonPress,bouncetime=bounceMillis)    
if __name__ == '__main__':
    main()
pygame.quit()
GPIO.cleanup()