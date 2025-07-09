import pandas as pd
import numpy as np
import os
import math
import itertools
import tensorflow as tf
import matplotlib.pyplot as plt
from keras.utils import multi_gpu_model
from keras import backend as K
from keras import regularizers
from keras.models import Sequential
from keras.layers import Dense, MaxoutDense, Dropout, Flatten, BatchNormalization, MaxPooling2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import Conv2D
from keras.utils import normalize, np_utils, multi_gpu_model, to_categorical
from keras.callbacks import TensorBoard, EarlyStopping, LearningRateScheduler, ModelCheckpoint
from keras.optimizers import SGD,Adagrad
from keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import precision_score, recall_score, f1_score, cohen_kappa_score
from sklearn.utils import class_weight
from keras.callbacks import Callback

img_rows, img_cols = 512,512 #i/p image rez
img_height, img_width = 512,512 #i/p image rez
channels = 3 #RGB image
classes = 5 #o/p classes

class change_lr(Callback):
    def __init__(self):
        super().__init__()
    '''
    def clr(self):
        Calculate the learning rate.
        l_r = 0.0003
        return l_r

    def on_epoch_begin(self, epoch, logs=None):
        #print(K.get_value(self.model.optimizer.lr))
        if epoch >= 4:
            return K.set_value(self.model.optimizer.lr, self.clr())
    '''
    
    def on_epoch_end(self, epoch, logs=None):
        #print('\nlr:- ', K.eval(self.model.optimizer.lr))
        #print('decay:- ', K.eval(self.model.optimizer.decay))

        lr = self.model.optimizer.lr
        decay = self.model.optimizer.decay
        iterations = self.model.optimizer.iterations
        lr_with_decay = lr / (1. + decay * K.cast(iterations, K.dtype(decay)))
        #print('Method_1_decay_applied:- ', K.eval(lr_with_decay))
        
        '''
        optimizer = self.model.optimizer
        _lr = tf.to_float(optimizer.lr, name='ToFloat') 
        _decay = tf.to_float(optimizer.decay, name='ToFloat')
        _iter = tf.to_float(optimizer.iterations, name='ToFloat')
        lr_decay = K.eval(_lr * (1. / (1. + _decay * _iter)))
        print('Method_2_LR: {:.20f}\n'.format(lr_decay))
        '''

        with open("model_parameters.txt", "a") as myfile:
            myfile.write("\n\nEpoch:- " + str(epoch))
            myfile.write("\nInitial_lr:- " + str(K.eval(self.model.optimizer.lr)))
            myfile.write("\nDecay:- " + str(K.eval(self.model.optimizer.decay)))
            myfile.write("\nlr_with_decay" + str(K.eval(lr_with_decay)))

def cnn_model(channels, nb_epoch, batch_size, nb_classes, nb_gpus, 
              leakiness, w_regu, b_regu, initializer, img_height, img_width,
              validation_data_dir, train_data_dir):

  '''
  #Sample data+labels path
  sample_data_dir = r"D:\Final Year Project\sample_cnn\sample.npy"
  sample_label = r"D:\Final Year Project\sample_cnn\sample.csv"

  sample_data= np.load(sample_data_dir)
  sam_labels = pd.read_csv(sample_label)
  sam_labels = sam_labels.values
  '''


  input_shape = (img_height,img_width,channels)
  '''
  Conv2D takes a 4D tensor as input_shape but we need to pass only
  3D while keras takes care of batch size on its own
  so pass (img_height,img_width,channels) not (batch_size,img_height,img_width,channels)
  '''

  model = Sequential()

  model.add(Conv2D(32,
                 (4,4),
                 strides=(2,2),
                 input_shape = input_shape,
                 padding='same',
                 ))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(Conv2D(32,
                 (4,4),
                 strides=(1,1),
                 padding='same',
                 ))
  model.add(BatchNormalization(axis = -1))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(MaxPooling2D(pool_size = (3, 3),
                       strides = (2, 2)))
  #model.add(Dropout(0.15))

  model.add(Conv2D(64,
                 (4, 4),
                 strides=(2, 2),
                 padding = 'same',
                 ))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(Conv2D(64,
                 (4, 4),
                 strides=(1, 1),
                 padding = 'same',
                 ))
  model.add(BatchNormalization(axis = -1))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(MaxPooling2D(pool_size = (2, 2),
                       strides = (2, 2)))
  #model.add(Dropout(0.20))

  model.add(Conv2D(128,
                 (4, 4),
                 strides = (1, 1),
                 padding = 'same',
                 ))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(Conv2D(128,
                 (4, 4),
                 strides = (1, 1),
                 padding = 'same',
                 ))
  model.add(BatchNormalization(axis = -1))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(MaxPooling2D(pool_size = (2, 2),
                       strides = (2, 2)))
  #model.add(Dropout(0.20))

  model.add(Conv2D(256,
                 (4, 4),
                 strides = (1, 1),
                 padding = 'same',
                 ))
  model.add(BatchNormalization(axis = -1))
  model.add(LeakyReLU(alpha = leakiness))

  model.add(MaxPooling2D(pool_size = (2, 2),
                       strides = (2, 2)))
  model.add(Conv2D(384,
                 (4, 4),
                 strides = (1, 1),
                 padding = 'same',
                 ))
  model.add(BatchNormalization(axis = -1))
  model.add(LeakyReLU(alpha = leakiness))

  model.add(MaxPooling2D(pool_size = (2, 2),
                       strides = (2, 2)))
  #model.add(Dropout(0.4))
  model.add(Conv2D(512,
                 (4, 4),
                 strides = (1, 1),
                 padding = 'same',
                 ))
  model.add(BatchNormalization(axis = -1))
  model.add(LeakyReLU(alpha = leakiness)) 
  model.add(MaxPooling2D(pool_size = (2, 2),
                       strides = (2, 2)))
##  model.add(Dropout(0.25))

  model.add(Flatten())

  model.add(Dense(1024))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(Dropout(0.5))
  model.add(Dense(1024))
  model.add(LeakyReLU(alpha = leakiness))
  model.add(Dropout(0.5))

  model.add(Dense(classes,activation = 'softmax'))

  model.summary()

  model = multi_gpu_model(model, gpus=2)
  
  #model.load_weights("C:\\Tirth\\Diabetic Retinopathy\\Model\\Train_again_on_saved model\\saved_model\\saved_epoch_10.h5")
  
  sgd = SGD(lr = 0.0001,momentum=0.9, decay= 1e-6 ,nesterov=True)

  model.compile(optimizer = sgd,
              loss = 'mean_squared_error',
              metrics = ['accuracy'])
  tensorboard = TensorBoard(log_dir = 'log/', histogram_freq = 0, write_graph = True,
                              write_images = True)
  stop = EarlyStopping(monitor = 'loss', patience = 0, verbose = 2, mode = 'auto')
  model_chkpt = ModelCheckpoint(filepath='saved_model/best_model/model_weights_Epoch_{epoch:02d}-ValLoss_{val_loss:.2f}.h5', monitor='val_loss')


  train_datagen = ImageDataGenerator(rescale = 1./255)

  train_generator = train_datagen.flow_from_directory(train_data_dir,
                                                      target_size = (img_height, img_width),
                                                      class_mode = 'categorical',
                                                      color_mode = 'rgb',
                                                      batch_size = batch_size,
                                                      shuffle = True)
  validation_generator = train_datagen.flow_from_directory(validation_data_dir,
                                                           target_size = (img_height, img_width),                            
                                                           class_mode = 'categorical',
                                                           color_mode = 'rgb',
                                                           batch_size = batch_size,
                                                           shuffle = True)

  lrChange = change_lr()
  
  STEP_SIZE_TRAIN = train_generator.n // train_generator.batch_size
  STEP_SIZE_VALID = validation_generator.n // validation_generator.batch_size
  model.fit_generator(train_generator,
                    steps_per_epoch = STEP_SIZE_TRAIN,
                    validation_data = validation_generator,
                    validation_steps = STEP_SIZE_VALID,
                    epochs = nb_epoch,
                    verbose = 1, max_queue_size = 60, workers= 6, use_multiprocessing = True,
                    callbacks = [stop, tensorboard, model_chkpt, lrChange])

  return model, validation_generator, train_generator



def plot_confusion_matrix(cm,
                          target_names,
                          title='Confusion matrix',
                          cmap=None,
                          normalize=True):
    """
    given a sklearn confusion matrix (cm), make a nice plot

    Arguments
    ---------
    cm:           confusion matrix from sklearn.metrics.confusion_matrix

    target_names: given classification classes such as [0, 1, 2]
                  the class names, for example: ['high', 'medium', 'low']

    title:        the text to display at the top of the matrix

    cmap:         the gradient of the values displayed from matplotlib.pyplot.cm
                  see http://matplotlib.org/examples/color/colormaps_reference.html
                  plt.get_cmap('jet') or plt.cm.Blues

    normalize:    If False, plot the raw numbers
                  If True, plot the proportions

    Usage
    -----
    plot_confusion_matrix(cm           = cm,                  # confusion matrix created by
                                                              # sklearn.metrics.confusion_matrix
                          normalize    = True,                # show proportions
                          target_names = y_labels_vals,       # list of names of the classes
                          title        = best_estimator_name) # title of graph

    Citiation
    ---------
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

    """
    if not os.path.exists('Confusion_Matrix'):
        os.makedirs('Confusion_Matrix')
        print("Confusion Matrix Folder Created!")

    accuracy = np.trace(cm) / float(np.sum(cm))
    misclass = 1 - accuracy

    if cmap is None:
        cmap = plt.get_cmap('Blues')

    plt.figure(figsize=(6, 8))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        plt.xticks(tick_marks, target_names, rotation=45)
        plt.yticks(tick_marks, target_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]


    thresh = cm.max() / 1.5 if normalize else cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if normalize:
            plt.text(j, i, "{:0.4f}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        else:
            plt.text(j, i, "{:,}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")


    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label\naccuracy={:0.4f}; misclass={:0.4f}'.format(accuracy, misclass))
    #plt.show()
    plt.savefig(str(title) + '.png')





