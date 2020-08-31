from pykinect2 import PyKinectV2, PyKinectRuntime
from pykinect2.PyKinectV2 import *
from arrowclass import *
import ctypes, _ctypes, pygame, sys, math, random, time, pyaudio, numpy, copy, os, wave
from array import array
from struct import pack


#Code modified from https://people.csail.mit.edu/hubert/pyaudio/
#plays wav file
def play(file):
    CHUNK = 1024 #measured in bytes
    wf = wave.open(file, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(CHUNK)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()

#the following functions are the read and write functions from cmu cs 15112
#course notes
def readFile(path):
    with open(path, "rt") as f:
        return f.read()
    
def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)

def distance(x1,y1,x2,y2):
    return int((((x1-x2)**2)+(y1-y2)**2))**(.5)

#https://github.com/fletcher-marsh/kinect_python/blob/master/FlapPyKinect.py
#The Kinect framework is from the 112 course

#gameruntime class in which entire game runs
class GameRuntime(object):
    def __init__(self):
        pygame.init()
        self.screenWidth = 1920
        self.screenHeight = 1080
        self.rightHandX = 0
        self.leftHandX = 0
        self.rightHandY = 0
        self.leftHandY = 0
        self.add = 5
        self.username = ''
        self.scoreList = []
        self.usernameList = []
        danceImg = pygame.image.load('dancescreen.png')
        self.img = danceImg.get_rect(topleft=(0,0))
        #arrow locations
        self.rightX = self.screenWidth // 2
        self.rightY = self.screenHeight//2
        self.leftX = self.screenWidth // 2
        self.leftY = self.screenHeight // 2
        self.type = []
        self.i = 0
        self.upLeft = []
        self.upRight = []
        self.lowLeft = []
        self.lowRight = []
        self.justLeft = []
        self.justRight = []
        self.back = False
        self.arrows = []
        self.score = 0
        self.begin = False
        self.timePassed = 0
        self.active = False
        self.song = ''
        self.showSongs = False 
        self.playSong = 'first'
        self.drawStart = False
        self.stop = False
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((960,540),
                                              pygame.HWSURFACE|pygame.DOUBLEBUF,
                                              32)
        self.done = False
        self.kinect = PyKinectRuntime.PyKinectRuntime(
            PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)
        self.playerScreen = pygame.Surface((self.kinect.color_frame_desc.Width,
                                            self.kinect.color_frame_desc.Height), 0, 32)
        self.frameSurface = pygame.Surface((self.kinect.color_frame_desc.Width,
                                            self.kinect.color_frame_desc.Height), 0, 32)
        self.bodies = None
        self.start = False
        self.centerX = 50
        self.centerY = 0
        self.centerWidth = 150
        self.centerHeight = 50
        self.enterName = False
        self.do = False
        self.displayType = True
        self.uploadX = self.centerX
        self.uploadY = self.centerY + 100
        self.uploadWidth = 150
        self.uploadHeight = 50
        self.showBox = False
        self.deleteAll = False
        self.powerScores = []
        self.doubleScore = False
        self.cooldown = 300
        self.streak = []
        self.powerUp = False
        self.existingX = self.centerX
        self.existingY = self.centerY + 200
        self.existingSongs = ['Believer','Never Say Never',
                              'Immortals','Stitches',
                              'Old Town Road','Thunderclouds',
                              'Sucker','Paradise']

        self.existingWavs = []
        self.existingRects = []
        self.firstBeat = 0
        self.choose = False
        self.box = ''
        self.showDirs = True

    #checks collisions between hands and arrows
    def collision(self):
        arrows = copy.copy(self.arrows)
        for arrow in arrows:
            if distance(self.rightHandX,self.rightHandY,arrow.x,arrow.y) <= 200:
                return True
            elif distance(self.leftHandX,self.leftHandY,arrow.x,arrow.y) <= 200:
                return True
    #draws score on the screen        
    def drawScore(self):
        font = pygame.font.Font(None, 100)
        text = font.render(("Score: " + str(self.score)), 1, (85,85,85))
        self.frameSurface.blit(text, (1200,300))

    def drawColorFrame(self, frame, targetSurface):
        targetSurface.lock()
        address = self.kinect.surface_as_array(targetSurface.get_buffer())
        ctypes.memmove(address, frame.ctypes.data, frame.size)
        del address
        targetSurface.unlock()

    #draws arrow heads--some of the code is taken from hw8.py Rocket class
    def drawArrowHeads(self,surface):
        size = 60
        angleChange = 2*math.pi/3
        dirX = 4
        ang = math.atan(self.screenHeight/self.screenWidth)
        dirY = int(float(math.tan(ang)*dirX))
        numPoints = 3
        points = []
        #upRight Arrow
        angle = math.atan(self.screenHeight/self.screenWidth)
        for point in range(numPoints):
            points.append((self.screenWidth-100 + size*math.cos(angle + point*angleChange),
                           100 - size*math.sin(angle + point*angleChange)))
        points.insert(numPoints-1, (self.screenWidth-100,100))   
        pygame.draw.polygon(surface,(0,0,0),points)
        points = []
        #upLeft Arrow
        angle = math.pi-math.atan(self.screenHeight/self.screenWidth)
        for point in range(numPoints):
            points.append((100 + size*math.cos(angle + point*angleChange),
                           100 - size*math.sin(angle + point*angleChange)))
        points.insert(numPoints-1, (100,100))   
        pygame.draw.polygon(surface,(0,0,0),points)
        points = []
        #downLeft Arrow
        angle = math.atan(self.screenHeight/self.screenWidth) + math.pi
        for point in range(numPoints):
            points.append((100 + size*math.cos(angle + point*angleChange),
                           self.screenHeight-100 - size*math.sin(angle + point*angleChange)))
        points.insert(numPoints-1, (100,self.screenHeight-100))   
        pygame.draw.polygon(surface,(0,0,0),points)
        points = []
        #downRight Arrow
        angle = -math.atan(self.screenHeight/self.screenWidth)
        for point in range(numPoints):
            points.append((self.screenWidth-100+ size*math.cos(angle + point*angleChange),
                           self.screenHeight-100 - size*math.sin(angle + point*angleChange)))
        points.insert(numPoints-1, (self.screenWidth-100,self.screenHeight-100))   
        pygame.draw.polygon(surface,(0,0,0),points)
        points = []
        #justLeft Arrow
        angle = math.pi
        for point in range(numPoints):
            points.append((100 + size*math.cos(angle + point*angleChange),
                           self.screenHeight//2 - size*math.sin(angle + point*angleChange)))
        points.insert(numPoints-1, (100,self.screenHeight//2))   
        pygame.draw.polygon(surface,(0,0,0),points)
        points = []
        #justRight Arrow
        angle = 0
        for point in range(numPoints):
            points.append((self.screenWidth-100 + size*math.cos(angle + point*angleChange),
                           self.screenHeight//2 - size*math.sin(angle + point*angleChange)))
        points.insert(numPoints-1, (self.screenWidth-100,
        self.screenHeight//2))   
        pygame.draw.polygon(surface,(0,0,0),points)
        points = []
        
    #the loop in which the game goes on until the song ends
    def writeArrows(self):
        end = False
        newnsn = readFile('neversaynever.txt')
        beats = newnsn.split('\n')
        findLastLine = []
        findPitch = []
        hangingNotes = readFile('hangingnotes.txt')
        notes = hangingNotes.split('\n')
        pitches = readFile('pitches.txt')
        pitchy = pitches.split('\n')
        count = 1
        start = time.time()
        for i in range(len(beats)):
            if count == 1 or count == 8: #these numbers are to get every
                #8th beat (too many beats are produced otherwise)
                findLastLine.append(beats[i])
                findPitch.append(pitchy[i])
            count += 1
            if count == 9: 
                count = -5
        self.count = findLastLine[0]      
        move = False
        count = 0
        self.timePassed += 1
        #while the count is less than num beats in the song and song is
        #not over
        while count < len(findLastLine) and self.stop == False:
            endTime = time.time() - start
            self.drawArrowHeads(self.frameSurface)
            self.drawScore()
            if self.showDirs == True:
                font = pygame.font.Font(None, 80)
                text = font.render("Use your hands to make the moves as they come down!", 1, (255,100,100))
                self.frameSurface.blit(text, (150,100))
                
                font = pygame.font.Font(None, 80)
                text = font.render('Avoid red arrows, which decrease your score!', 1, (255,100,100))
                self.frameSurface.blit(text, (150,200))                
                
                font = pygame.font.Font(None, 70)
                text = font.render('Press any key to quit', 1, (255,100,100))
                self.frameSurface.blit(text, (150,270))
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    self.stop = True
                if event.type == pygame.QUIT: # If user clicked close
                    self.done = True
                    self.kinect.close()
                    pygame.quit()
            #doubleScore powerUp: twice the points are earned
            if self.score >= 1 and self.score <= 15:
                self.doubleScore = True
            if self.score > 20:
                self.doubleScore = False
            #produces obstacle Arrows
            if self.score % 5 == 0 and self.score != 0 and (self.score
            not in self.powerScores):
                arrowDir = random.choice(['oL','oR'])
                dirX = 7
                ang = math.atan(self.screenHeight/self.screenWidth)
                dirY = int(float(math.tan(ang)*dirX))
                if arrowDir == 'oL':
                    arrow = obstacleLeftArrow(self.rightX, self.rightY,
                    dirX,dirY)
                elif arrowDir == 'oR':
                    arrow = obstacleRightArrow(self.rightX, self.rightY,
                    dirX,dirY)
                self.arrows.append(arrow)
                self.powerScores.append(self.score)
            if self.doubleScore == True:
                text = font.render("Double Score Activated!",
                    1, (85,85,85))
                self.frameSurface.blit(text, (self.screenWidth//3-100,
                self.screenHeight//3-200))
            #kinect framework
            hToW = float(self.frameSurface.get_height())/self.frameSurface.get_width()
            targetHeight = int(hToW * self.screen.get_width())
            surfaceToDraw = pygame.transform.scale(self.frameSurface,
             (self.screen.get_width(), targetHeight));
            self.screen.blit(surfaceToDraw, (0,0))
            surfaceToDraw = None
            pygame.display.update()
            if self.kinect.has_new_color_frame():
                frame = self.kinect.get_last_color_frame()
                self.drawColorFrame(frame, self.frameSurface)
                frame = None
            if self.kinect.has_new_body_frame():
                self.bodies = self.kinect.get_last_body_frame()
                if self.bodies is not None:
                    for i in range(0, self.kinect.max_body_count):
                        body = self.bodies.bodies[i]
                        if not body.is_tracked:
                            continue
                        joints = body.joints
                        self.showDirs = False
                        #right hand code
                        self.rightHandX = (int(self.screenWidth * joints[PyKinectV2.JointType_HandRight].Position.x))+self.screenWidth//2
                        if joints[PyKinectV2.JointType_HandRight].Position.y <= 0:
                            self.rightHandY = self.screenHeight//2 + abs(int(self.screenHeight * joints[PyKinectV2.JointType_HandRight].Position.y))
                        elif joints[PyKinectV2.JointType_HandRight].Position.y > 0:
                            self.rightHandY = self.screenHeight//2 -abs(int(self.screenHeight * joints[PyKinectV2.JointType_HandRight].Position.y))
                        #left hand code
                        self.leftHandX = (abs(int(self.screenWidth * joints[PyKinectV2.JointType_HandLeft].Position.x)))
                        if joints[PyKinectV2.JointType_HandLeft].Position.y <= 0:
                            self.leftHandY = self.screenHeight//2 + abs(int(self.screenHeight * joints[PyKinectV2.JointType_HandLeft].Position.y))
                        elif joints[PyKinectV2.JointType_HandLeft].Position.y > 0:
                            self.leftHandY = self.screenHeight//2 -abs(int(self.screenHeight * joints[PyKinectV2.JointType_HandLeft].Position.y))
                        time1 = round(float(endTime),1)
                        beat = round(float(findLastLine[count]),1)
                        if time1 > beat:
                            count += 1
                        beat = round(float(findLastLine[count]),1)
                        #if time passed is close to the beat, make an arrow
                        if math.isclose(time1,beat):
                            if findPitch[count] in notes:
                                dirX = 4
                                ang = math.atan(
                                    self.screenHeight/self.screenWidth)
                                dirY = int(float(math.tan(ang)*dirX))
                                arrow = hangingArrow(
                                    self.rightX+count, self.rightY,
                                    dirX,dirY)
                                self.arrows.append(arrow)
                            if self.score % 12 == 0 and self.score != 0 and (
                            self.score not in self.powerScores):
                                font = pygame.font.Font(None, 60)
                                text = font.render("Pop All Arrows Activated!",
                                 1, (85,85,85))
                                self.screen.blit(text, (self.screenWidth//5-200,
                                self.screenHeight//3-300))
                                pygame.display.update()
                                pygame.time.delay(800)
                                self.powerScores.append(self.score)
                                self.score += len(self.arrows)
                                self.arrows = []
                            else: 
                                arrowDir = random.choice(['upL','upR',
                                'lowR','lowL','L','R'])                     
                                dirX = 4
                                ang = math.atan(self.screenHeight/self.screenWidth)
                                dirY = int(float(math.tan(ang)*dirX))
                                if arrowDir == 'upL':
                                    arrow = upLeftArrow(self.rightX, self.rightY,
                                    dirX,dirY)
                                    self.arrows.append(arrow)
                                    self.upLeft.append(arrow)
                                elif arrowDir == 'upR':
                                    arrow = upRightArrow(self.rightX, self.rightY,
                                    dirX,dirY)
                                    self.arrows.append(arrow)
                                    self.upRight.append(arrow)
                                if arrowDir == 'L':
                                    arrow = justLeftArrow(self.rightX, self.rightY,
                                    dirX,dirY)
                                    self.arrows.append(arrow)
                                    self.justLeft.append(arrow)
                                if arrowDir == 'R':
                                    arrow = justRightArrow(self.rightX, self.rightY,
                                    dirX,dirY)
                                    self.arrows.append(arrow)
                                    self.justRight.append(arrow)
                                if arrowDir == 'lowL':
                                    arrow = lowLeftArrow(self.rightX, self.rightY,
                                    dirX,dirY)
                                    self.arrows.append(arrow)
                                    self.lowLeft.append(arrow)
                                if arrowDir == 'lowR':
                                    arrow = lowRightArrow(self.rightX, self.rightY,
                                    dirX,dirY)
                                    self.arrows.append(arrow)
                                    self.lowRight.append(arrow)
                            count += 1
                        for arrow in self.arrows:
                            arrow.move()
                            arrow.draw(self.frameSurface) 
                            arrow.drawArrowLine(self.frameSurface)
                            if arrow.offscreen() == True:
                               self.arrows.remove(arrow)
                            if self.playSong == 'first':
                                pygame.mixer.music.load(self.song)
                                pygame.mixer.music.play(0)
                                self.playSong = False                                    
                            if type(arrow) == hangingArrow:
                                i = arrow.collision(self.rightHandX,
                        self.rightHandY)
                                j = arrow.collision(self.leftHandX,
                        self.leftHandY)
                                if i != []:
                                    for ans in i:
                                        if ans < len(arrow.coords) and (
                                        arrow.coords[ans] in arrow.coords):
                                            arrow.coords.remove(
                                                arrow.coords[ans])
                                            self.score += 1
                                if j != []: 
                                    for ans in j:
                                        if ans < len(arrow.coords) and (
                                        arrow.coords[ans] in arrow.coords):
                                            arrow.coords.remove(
                                                arrow.coords[ans])
                                            self.score += 1
                            else:   
                                if arrow.collision(self.rightHandX,
                                self.rightHandY):
                                    if type(arrow) == obstacleLeftArrow:
                                        self.score -= 1
                                    elif type(arrow) == obstacleRightArrow:
                                        self.score -= 1
                                    else:
                                        if self.doubleScore == True:
                                            self.score += 2
                                        else:
                                            self.score += 1
                                    self.arrows.remove(arrow) 
                                if arrow.collision(self.leftHandX,
                                self.leftHandY):
                                    if type(arrow) == obstacleLeftArrow:
                                        self.score -= 1
                                    elif type(arrow) == obstacleRightArrow:
                                        self.score -= 1
                                    else:
                                        if self.doubleScore == True:
                                            self.score += 2
                                        else:
                                            self.score += 1
                                    self.arrows.remove(arrow)
        self.stop = True

    def drawArrows(self):
        for pair in self.upLeft:
            pygame.draw.circle(self.frameSurface,
                            (0,150,0),(pair[0],pair[1]), 100)
        for pair in (self.upRight):
            pygame.draw.circle(self.frameSurface,
                            (0,150,0),(pair[0],pair[1]), 100)
    #draws the back button
    def drawBackButton(self):
        pygame.draw.rect(self.screen,(0,0,0),
        pygame.Rect(800, 0,
        self.centerWidth+100, self.centerHeight))
        font = pygame.font.Font(None, 40)
        text = font.render("Back", 1, (85,85,85))
        self.screen.blit(text, (850, self.centerY))
        
    #draws the scoreboard screen
    def drawScoreboard(self):
        scoreboard = readFile('scoreboard.txt')
        scoring = scoreboard.split('\n')
        font = pygame.font.Font(None, 40)
        for score in scoring:
            lists = score.split(',')
            if len(lists) > 1: #if there is a name and score (len 2)
                self.usernameList.append(lists[0])
                self.scoreList.append(int(lists[1]))    
        findMax = []
        found = False
        i=0
        scoreList= copy.deepcopy(self.scoreList)
        while found == False:
            topScore = max(scoreList)
            ind = self.scoreList.index(topScore)
            self.scoreList[ind] = -1
            scoreList.remove(topScore)
            if [topScore,self.usernameList[ind]] not in findMax:
                findMax.append([topScore,self.usernameList[ind]])
            if len(findMax) == 5:
                found = True 
        for i in range(len(findMax)):
            pygame.draw.rect(self.screen,((102,205,170)),
            pygame.Rect(self.screenWidth//12, self.centerY + 100 + (i*50),
                self.uploadWidth, self.uploadHeight))
            text = font.render(str(i+1), 1, ((85,85,85)))
            self.screen.blit(text, (self.screenWidth//12 + 70,
                                        self.centerY + 100 + (i*50)))
            
            pygame.draw.rect(self.screen,((142,229,238)),
            pygame.Rect(self.screenWidth//5-30, self.centerY + 100 + (i*50),
                self.uploadWidth+100, self.uploadHeight))
            text = font.render(str(findMax[i][1]), 1, ((85,85,85)))
            self.screen.blit(text, (self.screenWidth//5 + self.uploadWidth//3.5,
                                        self.centerY + 100 + (i*50)))
            
            pygame.draw.rect(self.screen,(72,61,139),
            pygame.Rect(self.screenWidth//3, self.centerY + 100 + (i*50),
                self.uploadWidth, self.uploadHeight))
            text = font.render(str(findMax[i][0]), 1, ((85,85,85)))
            self.screen.blit(text, (self.screenWidth//3 + self.uploadWidth//2,
                                        self.centerY + 100 + (i*50)))
      
        text = font.render('Rank:', 1, ((85,85,85)))
        self.screen.blit(text, (self.screenWidth//12 + 30,
                                    self.centerY + 50))
     
        text = font.render('Name:', 1, ((85,85,85)))
        self.screen.blit(text, (self.screenWidth//6 + 30,
                                    self.centerY + 50))
       
        text = font.render('Score', 1, ((85,85,85)))
        self.screen.blit(text, (self.screenWidth//3 + 30,
                                    self.centerY + 50))
    #draws start button 
    def drawStartButton(self):
        pygame.draw.rect(self.screen,(0,0,0),
        pygame.Rect(self.centerX, self.centerY,
        self.centerWidth, self.centerHeight))
        font = pygame.font.Font(None, 40)
        text = font.render("Start", 1, (85,85,85))
        self.screen.blit(text, (self.centerX, self.centerY))

    #draws upload button   
    def drawUploadButton(self):
        pygame.draw.rect(self.screen,(0,0,0),
        pygame.Rect(self.uploadX-40, self.uploadY,
        self.uploadWidth, self.uploadHeight))
        font = pygame.font.Font(None, 30)
        text = font.render("Upload", 1, (85,85,85))
        self.screen.blit(text, (self.uploadX-20, self.uploadY))

    #draws choose song button
    def drawChoose(self):
        pygame.draw.rect(self.screen,(0,0,0),
        pygame.Rect(self.existingX-40, self.existingY,
        self.uploadWidth, self.uploadHeight))
        font = pygame.font.Font(None, 30)
        text = font.render("Choose Song", 1, (85,85,85))
        self.screen.blit(text, (self.existingX-20, self.existingY))

    #draws scoreboard button  
    def drawScoreboardButton(self):
        pygame.draw.rect(self.screen,(0,0,0),
        pygame.Rect(self.existingX-40, self.existingY+100,
        self.uploadWidth, self.uploadHeight))
        font = pygame.font.Font(None, 30)
        text = font.render("Scoreboard", 1, (85,85,85))
        self.screen.blit(text, (self.existingX-20, self.existingY+100))

    #draws box in which user types name or song to upload
    def drawTypeBox(self):
        pygame.draw.rect(self.screen,(0,0,0),
        pygame.Rect(400, 200,
        150+self.add, self.uploadHeight))
        
    #draws existing songs onto the screen    
    def drawExistingSongs(self):
        for i in range(len(self.existingSongs)):
            firstWav = self.existingSongs[i].replace(" ","")
            secondWav = firstWav.lower()
            finalWav = secondWav + ".wav"
            self.existingWavs.append(finalWav)
            pygame.draw.rect(self.screen,(125,158,192),
            pygame.Rect(self.screenWidth//6, self.centerY + (i*50),
                self.uploadWidth+100, self.uploadHeight))
            self.existingRects.append(pygame.Rect(
                    self.screenWidth//6, self.centerY + (i*50),
                self.uploadWidth+100, self.uploadHeight))            
            font = pygame.font.Font(None, 40)
            text = font.render(str(self.existingSongs[i]), 1, (85,85,85))
            self.screen.blit(text, (self.screenWidth//6+10,
                                        self.centerY + (i*50)))
    #collision detection when user clicks on screen                        
    def mousePressed(self,x,y):
        if self.begin == True:
            if pygame.Rect(self.centerX, self.centerY,
            self.centerWidth,
            self.centerHeight).collidepoint(x,y): #start button
                self.start = True
        if pygame.Rect(self.uploadX, self.uploadY,
        self.uploadWidth,
        self.uploadHeight).collidepoint(x,y): #upload button
            self.active = True
            img = pygame.transform.scale(
            pygame.image.load('uploadown.png').convert_alpha(),
                (960, 560))
            #image from
            #https://paperpull.com/dance-dance-revolution-x2-logo-wallpaper/
            self.screen.blit(img,[0,0])
            font = pygame.font.Font(None, 30)
            text = font.render('Type in .wav file!', 1, (85,85,85))
            self.screen.blit(text, (self.screenWidth//6+80,
                                        self.centerY + 100))
            self.drawBackButton()
        #back button
        if pygame.Rect(800, 0,
        self.centerWidth+100, self.centerHeight).collidepoint(x,y) and (
        self.active == True): 
            self.active = False
            self.song = ''
            self.run()
        if pygame.Rect(self.existingX, self.existingY+100,
        self.uploadWidth,
        self.uploadHeight).collidepoint(x,y):
            img = pygame.transform.scale(
                pygame.image.load('uploadown.png').convert_alpha(),
                (960, 560))
            self.screen.blit(img,[0,0])
            self.drawScoreboard()
            self.drawBackButton()
            self.back = True
        #back button
        if self.back == True:
            if pygame.Rect(800, 0,
    self.centerWidth+100, self.centerHeight).collidepoint(x,y):
                self.showSongs = False
                self.active = False
                self.begin = False
                self.song = ''
                self.run()
        if pygame.Rect(self.existingX, self.existingY,
        self.uploadWidth,
        self.uploadHeight).collidepoint(x,y): #if you click choose
            img = pygame.transform.scale(
                pygame.image.load('uploadown.png').convert_alpha(),
                (960, 560))
            self.screen.blit(img,[0,0])
            self.drawExistingSongs()
            self.drawBackButton()
            self.do = True
        if self.do == True:
            for i in range(len(self.existingRects)):
                #finds song clicked on from existing songs screen
                if self.existingRects[i].collidepoint(x,y):
                    self.song = self.existingWavs[i]
            if pygame.Rect(800, 0,
    self.centerWidth+100, self.centerHeight).collidepoint(x,y):
                self.showSongs = False
                self.active = False
                self.begin = False
                self.run()
            if self.song != '':
                #if there exists a song, draw start button
                self.drawStartButton()
                self.begin = True
                if self.begin == True: 
                    if pygame.Rect(self.centerX, self.centerY,
                    self.centerWidth,
                    self.centerHeight).collidepoint(x,y): #start button
                        self.start = True
                        
    def keyPressed(self,key,unicode):
        font = pygame.font.Font(None, 40)
        if self.active == True and self.enterName != True:
            img = pygame.transform.scale(
            pygame.image.load('uploadown.png').convert_alpha(),
                (960, 560))
            self.screen.blit(img,[0,0])
            self.drawBackButton()
            if key == pygame.K_RETURN:
                exists = os.path.isfile(str(self.box))
                if exists:
                    self.song = self.box   
                    self.drawStartButton()
                    self.begin = True
                else:
                    text = font.render("Song not found in directory.",
                                        1, (85,85,85))
                    self.screen.blit(text, (self.screenWidth//6,
                                            self.screenHeight//4 + 100))
                    text = font.render("Please enter another song.",
                                        1, (85,85,85))
                    self.screen.blit(text, (self.screenWidth//6,
                                            150 + self.screenHeight//4))
                    pygame.time.wait(400)
            if key == pygame.K_BACKSPACE: 
                song = self.box
                if song == '':
                    lastChar = ''
                else:
                    lastChar = song[-1]
                self.box = self.box[:-1]
                self.add -= font.size(lastChar)[0] #font size returns
                #(font width, font height), so only use the width
            elif key != pygame.K_RETURN:
                self.box += unicode
                #changes size of box depending on font size
                if font.size(str(self.box))[0] > self.uploadWidth+self.add:
                    song = self.box
                    lastChar = song[-1]
                    self.add += font.size(lastChar)[0]
            self.drawTypeBox()
            text = font.render(str(self.box),1,(85,85,85))
            self.screen.blit(text,(self.centerX+350,
            self.centerY + 200))
        
        if self.enterName == True:
            if key == pygame.K_RETURN:
                if self.username != '':
                    #writes to scoreboard
                    #inspiration for code from
                    #https://www.dreamincode.net/
                    #forums/topic/198139-reading-
                    #and-writing-to-a-txt-file-in-python/
                    f = open("scoreboard.txt", "a")
                    f.write(str(self.username) + "," + str(self.score) + "\n")
                    f.close()
                    text = font.render("Thanks for playing!",1,(85,85,85))
                    self.screen.blit(text,(self.centerX+350,
                    self.centerY + 500))
                    pygame.display.update()
                    pygame.time.wait(2000)
                    self.done = True
                    self.kinect.close()
                    pygame.quit()
                else: 
                    text = font.render("Please type at least one letter!",
                                        1, (85,85,85))
                    self.screen.blit(text, (self.screenWidth//6,
                                            self.screenHeight//4))
                    pygame.time.wait(400)
            if key == pygame.K_BACKSPACE: 
                song = self.username
                lastChar = song[-1]
                self.username = self.username[:-1]
                self.add -= font.size(lastChar)[0]
            elif key != pygame.K_RETURN:
                self.username += unicode
                #box width changes depending on text size
                if font.size(str(self.username))[0] > self.uploadWidth+self.add:
                    song = self.username
                    lastChar = song[-1]
                    self.add += font.size(lastChar)[0]    
            self.drawTypeBox()
            text = font.render(str(self.username),1,(85,85,85))
            self.screen.blit(text,(self.centerX+350,
            self.centerY + 200))
                
    def run(self):
        danceImg = pygame.image.load('dancescreen.png')
        #image from
        #https://emumovies.com/
        #files/file/2882-heres-my-realistic-
        #dance-dance-revolution-arcade-bezels-for-mame/
        self.img = danceImg.get_rect(topleft=(0,0))
        img = pygame.transform.scale(
              pygame.image.load('dancescreen.png').convert_alpha(),
                (960, 560))
        self.screen.blit(img,[0,0])
        self.drawUploadButton()
        self.drawChoose()
        self.drawScoreboardButton()
        while not self.done:
            font = pygame.font.Font(None, 40)
            if self.start == False:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.mousePressed(*(event.pos))
                    elif event.type == pygame.KEYDOWN:
                        self.keyPressed(event.key,event.unicode)
                    if event.type == pygame.QUIT: # If user clicked close
                        self.done = True
                        self.kinect.close()
                        pygame.quit()
                pygame.display.update()
            else: #if game has started
                self.timePassed += 1
                if self.stop != True: 
                    self.writeArrows()
                if self.displayType == True:
                    text = font.render('Type to Enter Name!',1,(255,200,200))
                    self.screen.blit(text,(self.centerX+250,
                    self.centerY + 150))
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.done = True
                        if event.type == pygame.KEYDOWN and self.stop == True:
                            self.enterName = True
                            self.keyPressed(event.key,event.unicode)
            pygame.display.update()
            self.clock.tick(60) #runs 60 frames per second
        self.kinect.close()
        pygame.quit()        
#runs game
game = GameRuntime();
game.run();
