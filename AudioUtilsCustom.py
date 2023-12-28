from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import cosine_similarity
import librosa as lr
import numpy as np
import scipy.signal as signal
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.io import wavfile
import re


"""
쓰레기함수모음집
"""


#Plotting
def plot_waveform(sample, isLibrosa = False):

    plt.figure(figsize=(12, 4))
    if isLibrosa:
        plt.plot(sample, label="Combined Audio Waveform")
    else:
        plt.plot(np.mean(sample, axis=1), label="Combined Audio Waveform")
    plt.title("Stereo Audio Waveform")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.show()
#Plotting with bounds
def plot_waveform_withBounds(sample, non_silent_segments , isLibrosa = False):
    plt.figure(figsize=(12, 4))
    if isLibrosa:
        plt.plot(sample, label="Combined Audio Waveform")
    else:
        plt.plot(np.mean(sample, axis=1), label="Combined Audio Waveform")
    for start, end in non_silent_segments:
        plt.axvline(x=start, color='green', linestyle='--', label="Segment Start")
        plt.axvline(x=end, color='red', linestyle='--', label="Segment End")
        #print(f"Non-silent segment: Start = {start}, End = {end}")

    plt.title("Stereo Audio with Non-Silent Segments")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    #plt.legend()
    plt.show()

def plot_spectrogram(spectrogram, samplerate):
    # Display the spectrogram
    plt.figure(figsize=(10, 4))
    lr.display.specshow(lr.amplitude_to_db(spectrogram, ref=np.max), sr=samplerate, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title('STFT Spectrogram')
    plt.show()
# sub-function of find_blocks
def has_consecutive_zeros(data, startindex, silence_threshold, window):
    if silence_threshold != 0:
        for i in range(window):
            if abs(data[startindex+i]) < 0:
                return False
        return True
    else:
        for i in range(window):
            if data[startindex+i] != 0:
                return False
        return True        

# Tokenize Audio - Very Basic
def find_blocks(data, silence_threshold = 0, window = 20, isLibrosa = False):

    # Calculate the minimum length for a segment based on minimum duration
    if isLibrosa:
        combined_data = data
    else:
        combined_data = np.mean(data, axis=1)
    # Initialize variables
    segments = []
    start_index = None

    # Iterate over the combined audio data
    for i, sample in enumerate(combined_data):
        if start_index is None: #and len(combined_data) - i > window: #edge case
            if combined_data[i] != 0: #if the sample is not 0
                start_index = i
        else: # if start index is not none
            if combined_data[i] == 0: #if the sample is 0
                if window > (len(combined_data) - start_index) or \
                has_consecutive_zeros(combined_data, i, silence_threshold, window): #check consecutive zeros
                    segments.append((start_index, i))
                    start_index = None

    # Check for the last segment
    if start_index is not None and len(combined_data) - start_index > window:
        segments.append((start_index, len(combined_data) - 20))

    return segments

#whether wav1 == wav2
def compare_exact(wav1, wav2, isLibrosa = False):
    if isLibrosa:
        for i in range(len(wav1)):
            if wav1[i] != wav2[i]:
                return False
    else:
        for i in range(len(wav1)):
            if wav1[i][0] != wav2[i][0] or wav1[i][1] != wav2[i][1]:
                return False
    return True


#두 audio segment의 길이를 같게 함
def match_list(listA, listB):
    if len(listA) > len(listB):
        listA = listA[:len(listB)]
    elif len(listA) < len(listB):
        listB = listB[:len(listA)]
    return listA, listB

#window_size(아마 10정도)로 해당 리스트의 값을 blur 함
def blur_list(target, window_size):
    return [np.mean(target[i:i+window_size]) for i in range(len(target) - window_size)]

def get_cosine_similarity(listA, listB):
    similarity = cosine_similarity([listA], [listB])
    return similarity[0][0]

#cosine similarity의 계산. 길이가 다른 경우도 고려함.
def compare_similar(listOrigin, listNew, isLibrosa = False):
    listA, listB = match_list(listOrigin, listNew)

    if isLibrosa == False:
        listA = np.mean(listA, axis=1)
        listB = np.mean(listB, axis=1)
    if len(listA) > 10 and len(listB) > 10:
        listA = blur_list(listA, 10)
        listB = blur_list(listB, 10)
    
    return get_cosine_similarity(listA, listB)

#compare_spectrogram의 하위 function
def get_spectrogram(data, max_fft = 2048):
    signal_length = len(data)
    n_fft = 2**int(np.floor(np.log2(signal_length)))
    n_fft = max(min(n_fft, max_fft), 4)
    spectrogram = np.abs(lr.stft(data, n_fft = n_fft))
    return spectrogram

#두 audio segment의 spectrogram을 형성 후 cosine similarity를 계산합니다.
def compare_spectrogram(data1, data2):
    dt1, dt2 = match_list(data1, data2)
    spectrogram1 = get_spectrogram(dt1)
    spectrogram2 = get_spectrogram(dt2)
    # Flatten the spectrogram data
    flat_spec1 = spectrogram1.flatten()
    flat_spec2 = spectrogram2.flatten()

    # Compute cosine similarity (1 - cosine distance)
    similarity = 1-cosine(flat_spec1, flat_spec2)
    return similarity

#Filename을 구하는데 사용함
def extract_filename(filepath):
    """Extract the filename from a full file path using regex."""
    match = re.search(r'[^\\]+$', filepath)
    return match.group() if match else None

