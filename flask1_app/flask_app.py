from flask import Flask
from flask import render_template,Flask
from flask import request
import os
import pickle
import numpy as np
import pandas as pd
import scipy
import sklearn
import skimage
import skimage.color
import skimage.transform
import skimage.feature
import skimage.io
app=Flask(__name__)

BASE_PATH=os.getcwd()
UPLOAD_PATH=os.path.join(BASE_PATH,'static/upload/')
MODEL_PATH=os.path.join(BASE_PATH,'static/models/')

##################### LOAD MODELS #####################
model_sgd_path=os.path.join(MODEL_PATH,'dsa_image_classification_sgd.pickle')
scaler_path=os.path.join(MODEL_PATH,'dsa_scaler.pickle')
model_sgd=pickle.load(open(model_sgd_path,'rb'))
scaler=pickle.load(open(scaler_path,'rb'))


@app.errorhandler(404)
def error404(error):
    message="ERROR 404 OCCURED. Page Not Found. Please go the home page and try again"
    return render_template("error.html",message=message)

@app.errorhandler(405)
def error404(error):
    message="ERROR 405 OCCURED. Method Not Found."
    return render_template("error.html",message=message)

@app.errorhandler(500)
def error404(error):
    message="INTERNAL ERROR 500, Error occurs in the program"
    return render_template("error.html",message=message)


@app.route('/',methods=["GET","POST"])
def index():
    if request.method=="POST":
        upload_file=request.files["image_name"]
        filename=upload_file.filename
        print("The filename that has been uploaded =",filename)
        # know the extention of the filename
        # allow only .jpg , .jpeg , .png
        ext=filename.split(".")[-1]
        print("The Extension of the filename =",ext)
        if ext.lower() in ['png','jpg','jpeg']:
            # Save the Image
            path_save=os.path.join(UPLOAD_PATH,filename)
            upload_file.save(path_save)
            print("The file Saved Successfully")
            hei=findHeight(path_save)
            # send to the PIpeline Model
            result=pipeline_model(path_save,scaler,model_sgd)
            print(result)
            return render_template('upload.html',fileupload=True,extension=False,data=result,image_filename=filename,height=hei)
            
        else:
            print('Use only the extension with .jpg, .png, .jpeg')
            return render_template('upload.html',extension=True,fileupload=False)
    return render_template('upload.html',fileupload=False,extension=False)
@app.route('/about/')
def about():
    return render_template('about.html')

def findHeight(path):
    img=skimage.io.imread(path)
    h,w,_=img.shape
    aspect=h/w
    given_width=300
    height=given_width*aspect
    return height

def pipeline_model(path,scaler_transform,model_sgd):
    # Pipeline Model
    image=skimage.io.imread(path)
    # Transform image into 80 X 80
    image_resize=skimage.transform.resize(image,(80,80))
    image_scale=255 * image_resize
    image_transform=image_scale.astype(np.uint8)
    # RGB to GRAY
    gray=skimage.color.rgb2gray(image_transform)
    # Hog Feature
    feature_vector=skimage.feature.hog(gray,orientations=10,pixels_per_cell=(8,8),
                                      cells_per_block=(2,2))
    # Scaling
    scalex=scaler_transform.transform(feature_vector.reshape(1,-1))
    result=model_sgd.predict(scalex)
    # Decision function # Confidence
    decision_value=model_sgd.decision_function(scalex).flatten()
    labels=model_sgd.classes_
    # probability
    z=scipy.stats.zscore(decision_value)
    prob_value=scipy.special.softmax(z)
    
    # Top 5
    top_5_prob_ind=prob_value.argsort()[::-1][:5]
    top_labels = labels[top_5_prob_ind]
    top_prob = prob_value[top_5_prob_ind]
    # put it in Dictionary
    top_dict={}
    for key,val in zip(top_labels,top_prob):
        top_dict.update({key:np.round(val,3)})
        
    return top_dict


if __name__=="__main__":
    app.run(debug=True)
