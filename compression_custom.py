from AudioUtilsCustom import *

class Audiopackage:
        
    def __init__(self, audiofile, parsetype = "spectrogram"):
        if parsetype != "exact" and parsetype != "similar" and parsetype != "spectrogram":
            print("Invalid parsetype")
            return
        self.name = extract_filename(audiofile)
        samplerate, audio = wavfile.read(audiofile)
        self.parsetype = parsetype
        #load audio as wavfile.
        self.samplerate = samplerate
        self.audio = audio
        #slice audio

        if self.parsetype == "spectrogram":
            self.lrfile, self.samplerate = lr.load(audiofile, sr = self.samplerate)
        
        self.audiosegmentlist = [] 
        self.audioIndex = find_blocks(audio) 
        self.length = len(self.audio)
        self.segmentSize = 0
        self.audioIndexSize = len(self.audioIndex)
        #print("AudioPackage Initialized")
        #print("Audio Length: ", self.length)
        #print("Audio Index length: ", self.audioIndex)
        self.parse()
    
    def lengthExists(self, i, duration):

        if duration == self.audiosegmentlist[i].length:
            #print("Length Exists")
            return True
        return False
    
    def lengthSimilar(self, i, duration):
        origin = self.audiosegmentlist[i].length
        if abs((duration - origin)/origin) < 0.1:
            #print("Length Similar")
            return True
        #print("Length Not Similar")
        return False
    
    def parse(self):
        #print(len(self.lrfile))
        #print("is the length of LR file")
        for i in range(self.audioIndexSize):
            if self.parsetype == "spectrogram":
                #print("Making it")
                target_lrfile = self.lrfile[self.audioIndex[i][0]:self.audioIndex[i][1]]
            #print(len(target_lrfile))
            #print("is the length of LR file")
            target = self.audio[self.audioIndex[i][0]:self.audioIndex[i][1]]
            start = self.audioIndex[i][0]
            end = self.audioIndex[i][1]
            duration = end - start
            if self.segmentSize == 0:
                #print("First Sample Added")
                if self.parsetype == "spectrogram":
                    self.audiosegmentlist.append(AudioSegment(target, duration, start, lrfile = self.lrfile[start:end], islibrosa=True))
                else:
                    self.audiosegmentlist.append(AudioSegment(target, duration, start))
                self.segmentSize += 1
            else:
                if self.parsetype == "exact":
                    self.apply_compare_exact(target, duration, start)
                elif self.parsetype == "similar":
                    self.apply_compare_similar(target, duration, start)
                elif self.parsetype == "spectrogram":
                    self.apply_compare_spectrogram(target, duration, start, target_lrfile)

    def apply_compare_exact(self, target, duration, start):

        for i in range(self.segmentSize):
            if self.lengthExists(i, duration) == True:
                if compare_exact(self.audiosegmentlist[i].audio, target) == True:
                    self.audiosegmentlist[i].append(start)
                    return
        #if no exact match, then append
        self.audiosegmentlist.append(AudioSegment(target, duration, start))
        self.segmentSize += 1

            
    def apply_compare_similar(self, target, duration, start):
        for i in range(self.segmentSize):
            if self.lengthSimilar(i, duration) == True:
                if compare_similar(self.audiosegmentlist[i].audio, target) > 0.99:
                    self.audiosegmentlist[i].append(start)
                    return
        self.audiosegmentlist.append(AudioSegment(target, duration, start))
        self.segmentSize += 1
    def apply_compare_spectrogram(self, target, duration, start, target_lrfile):
        for i in range(self.segmentSize):
            if self.lengthSimilar(i, duration) == True:
                if compare_spectrogram(self.audiosegmentlist[i].lrfile, target_lrfile) > 0.99:
                    self.audiosegmentlist[i].append(start)
                    return
        self.audiosegmentlist.append(AudioSegment(target, duration, start, lrfile = target_lrfile, islibrosa=True))
        self.segmentSize += 1
        # indexlist[9].append(index)
            #compare length first
            #if length is same, then compare each sample
        #else indexlist.append(AudioSegment(audio, length, index))



    def print(self):
        for i in range (len(self.audiosegmentlist)):
            print(self.audiosegmentlist[i])
    
    def sumSegments(self):
        ans = 0 
        for i in range(self.segmentSize):
            ans += self.audiosegmentlist[i].length
        return ans
    def compratio(self):
        return self.sumSegments()/self.length
    
    def printInfo(self):
        print("Audio Nane: ", self.name)
        print("Audio Length: ", self.length)
        #print("Audio Index length: ", self.audioIndex)
        print("Segment Size: ", self.segmentSize)
        #print("Audio Segment List: ", self.audiosegmentlist)
        print("Sum of Segments: ", self.sumSegments())
        print("Ratio of Compression: ", self.sumSegments()/self.length)


class AudioSegment:
    #처음 불릴때
    def __init__(self, audio, length, index, amplitude = 1, lrfile = None, islibrosa = False):
        self.indexlist = [index] 
        self.length = length
        self.audio = audio
        self.amplitude = amplitude

        self.lrfile = lrfile
    def __str__(self):
        return "SampleLength: " + str(self.length) + " , IndexList: " + str(self.indexlist)
    def append(self, index, amplitude = 1):
        #초기 샘플보다 후기 샘플이 더 adaptable 할 경우
        self.indexlist.append(index)