
import os
import glob
import pickle
import pandas as pd
import librosa
import numpy as np
from multiprocessing import Pool

from PIL import Image
with_loc_feature=False
def get_feature(filename,feature):
    try:
        print(filename)
        name,_ = os.path.splitext(filename)
        npy_path=name+".npy"
        feat=None
        if with_loc_feature and os.path.exists(npy_path):
            ## 10msec 16k
            feat=np.load(npy_path)
            feat=feat.transpose()
            #print("feat",feat.shape)
        y, sr = librosa.load(filename)
        #print("y;",y.shape)
        if feature=="mfcc":
            mfcc_feature = librosa.feature.mfcc(y=y,sr=sr,n_mfcc=13)
            mfcc_delta = librosa.feature.delta(mfcc_feature)
            mfcc_deltadelta = librosa.feature.delta(mfcc_delta)
            f=np.vstack([mfcc_feature, mfcc_delta,mfcc_deltadelta])
            if feat is not None:
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                f=np.concatenate([feat,f],axis=0)
                return f
            return f
        elif feature=="mel":
            S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
            logS = librosa.amplitude_to_db(S, ref=np.max)
            if feat is not None:
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                f=np.concatenate([feat,f],axis=0)
                return f
            return logS
        elif feature=="mel2":
            S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
            logS = librosa.amplitude_to_db(S, ref=np.max)
            logS_delta = librosa.feature.delta(logS)
            logS_deltadelta = librosa.feature.delta(logS)
            f=np.vstack([logS, logS_delta, logS_deltadelta])
            if feat is not None:
                #print("feat",feat.shape)
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                #print("feat",feat.shape)
                f=np.concatenate([feat,f],axis=0)
                #print("mel",f.shape)
                return f
            #print("mel",f.shape)
            return f
        elif feature=="spec":
            # win_length =n_fft
            # hop_length=win_length / 4
            D = librosa.stft(y,n_fft=1024,hop_length=None, win_length=None)
            log_power = librosa.amplitude_to_db(np.abs(D), ref=np.max)
            if feat is not None:
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                f=np.concatenate([feat,f],axis=0)
                return f
            return log_power
    except:
        print("[ERROR]",filename)
        return None

def process(args):
    filename,y,i,f=args
    if f=="":
        x=get_feature(filename,"mel")
    else:
        x=get_feature(filename,f)
    return (x,y,i)



def make_dataset(input_filename,feature,limit_length):
    all_data=[]
    for i,row in song_df.iterrows():
        filename=row["SepWaveFileName"]
        y=int(row["y"])
        if y>=0:
            all_data.append((filename,y,i,feature))

      
    p = Pool(38)
    results=p.map(process, all_data)
    p.close()

    all_data_x=[]
    all_data_y=[]
    all_data_idx=[]
    for r in results:
        x,y,idx=r
        if x is not None:
            all_data_x.append(x)
            all_data_y.append(y)
            all_data_idx.append(idx)

    ### output ###
    print("=== output ===")
    if output_path is not None:
        os.makedirs(output_path,exist_ok=True)

        label=[]
        idx=[]
        for (x,y,i) in zip(all_data_x,all_data_y,all_data_idx):
              label.append([y]*x.shape[1])
              idx.append([i]*x.shape[1])
        
        out_x=np.concatenate(all_data_x,axis=1)
        out_x=np.transpose(out_x)
        out_y=np.concatenate(label)
        out_idx=np.concatenate(idx)
        
        np.save(output_path + "/data_x."+feature+".npy",out_x)
        np.save(output_path + "/data_y."+feature+".npy",out_y)
        np.save(output_path + "/data_wav_index."+feature+".npy",out_idx)
        
        print("x:",out_x.shape)
        print("y:",out_y.shape)
        print("index:",out_idx.shape)
        ### 
    
    ### output ###
    if output_ex_path is not None:
        print("=== output (sequence) ===")
        os.makedirs(output_ex_path,exist_ok=True)

        steps=[x.shape[1] for x in all_data_x]
        max_step = max(steps)
        fs=[x.shape[0] for x in all_data_x]
        max_fs = max(fs)
        print("#sample :",len(all_data_x))
        print("max step:",max_step)
        print("feature :",max_fs)
        if limit_length is not None and limit_length<max_step:
            max_step=limit_length
        out_seq_x=np.zeros((len(all_data_x),max_step,max_fs))
        steps=[]
        for i,x in enumerate(all_data_x):
            s=x.shape[1]
            if limit_length is not None and limit_length<s:
                s=limit_length
            steps.append(s)
            out_seq_x[i,:s,:]=np.transpose(x)[:s,:]
        
        out_seq_s=np.array(steps)
        out_seq_y=np.array(all_data_y)
        out_seq_idx=np.array(all_data_idx)
        
        np.save(output_ex_path + "/data_x."+feature+".npy",out_seq_x)
        np.save(output_ex_path + "/data_s."+feature+".npy",out_seq_s)
        np.save(output_ex_path + "/data_y."+feature+".npy",out_seq_y)
        np.save(output_ex_path + "/data_wav_index."+feature+".npy",out_seq_idx)
        print("x:",out_seq_x.shape)
        print("s:",out_seq_s.shape)
        print("y:",out_seq_y.shape)
        print("index:",out_seq_idx.shape)
    ### 


def main():
    make_dataset()

if __name__ == '__main__':
    main()

