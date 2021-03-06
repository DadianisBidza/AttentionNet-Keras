import tensorflow as tf
import keras
import numpy as np
from keras import backend as K
from keras.models import Model
from keras.engine.topology import Layer
from keras.layers import Input
from keras.layers.core import Dense, Lambda, Activation, Flatten, Reshape
from keras.layers.convolutional import Conv2D
from keras.layers.merge import Concatenate, Add
from keras.layers.pooling import MaxPooling2D, AveragePooling2D
from keras.layers.normalization import BatchNormalization
from keras.callbacks import Callback, LearningRateScheduler, ModelCheckpoint, LambdaCallback, TensorBoard, EarlyStopping, ReduceLROnPlateau
from keras.optimizers import SGD
import winsound
import os



class StandardVGG:
    def __init__(self):
        inp = Input(shape=(32, 32, 3))
        regularizer = keras.regularizers.l2(0.0005)
        x = Conv2D(64, (3, 3), activation='relu', padding='same', name='block1_conv1', kernel_regularizer=regularizer)(inp)
        x = Conv2D(64, (3, 3), activation='relu', padding='same', name='block1_conv2', kernel_regularizer=regularizer)(x)
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block1_pool')(x)

        # Block 2
        x = Conv2D(128, (3, 3), activation='relu', padding='same', name='block2_conv1', kernel_regularizer=regularizer)(x)
        x = Conv2D(128, (3, 3), activation='relu', padding='same', name='block2_conv2', kernel_regularizer=regularizer)(x)
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block2_pool')(x)

        # Block 3
        x = Conv2D(256, (3, 3), activation='relu', padding='same', name='block3_conv1', kernel_regularizer=regularizer)(x)
        x = Conv2D(256, (3, 3), activation='relu', padding='same', name='block3_conv2', kernel_regularizer=regularizer)(x)
        x = Conv2D(256, (3, 3), activation='relu', padding='same', name='block3_conv3', kernel_regularizer=regularizer)(x)
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block3_pool')(x)

        # Block 4
        x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block4_conv1', kernel_regularizer=regularizer)(x)
        x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block4_conv2', kernel_regularizer=regularizer)(x)
        x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block4_conv3', kernel_regularizer=regularizer)(x)
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block4_pool')(x)

        # Block 5
        x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block5_conv1', kernel_regularizer=regularizer)(x)
        x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block5_conv2', kernel_regularizer=regularizer)(x)
        x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block5_conv3', kernel_regularizer=regularizer)(x)
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block5_pool')(x)

        x = Flatten(name='flatten')(x)
        x = Dense(4096, activation='relu', name='fc1', kernel_regularizer=regularizer)(x)
        x = Dense(4096, activation='relu', name='fc2', kernel_regularizer=regularizer)(x)
        x = Dense(10, activation='softmax', name='predictions', kernel_regularizer=regularizer)(x)

        self.model = Model(inp, x, name='vgg16')
        self.name = "VGG16"
        self.datasetname="cifar16"
        
        print("Generated "+self.name)

        optimizer=SGD(lr=1, momentum=0.9, decay=0.0000001)
        loss='categorical_crossentropy'
        metrics=['accuracy']
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
    
    def StandardFit(self, datasetname=None, X=[], Y=[], beep=False):
        Y = keras.utils.to_categorical(Y,self.outputclasses)
        if datasetname==None:
            datasetname=self.datasetname
        scheduler = LearningRateScaler(25, 0.5)
        startingepoch = 0
        pastepochs = list(map(int, [x.replace(".hdf5", "").replace(self.name+"-"+datasetname, "").replace(" ", "") for x in os.listdir("weights") if self.name+"-"+datasetname in x]))
        if len(pastepochs):
            if max(pastepochs) == 300:                
                print("Found completely trained weights for "+self.name+"-"+datasetname)
                return
            self.model.load_weights("weights/"+self.name+"-"+datasetname+" "+str(max(pastepochs))+".hdf5")
            startingepoch = max(pastepochs)
        tboardcb = TensorBoard(log_dir='./logs', histogram_freq=0, batch_size=3, write_graph=True, write_grads=False, write_images=False, embeddings_freq=0, embeddings_layer_names=None, embeddings_metadata=None)
        checkpoint = ModelCheckpoint("weights/"+self.name+"-"+datasetname+" {epoch}.hdf5", save_weights_only=True)
        epochprint = LambdaCallback(on_epoch_end=lambda epoch, logs: print("Passed epoch "+str(epoch)))
        callbackslist = [scheduler, checkpoint, epochprint, tboardcb]
        if beep:
            callbackslist.append(Beeper(1))
        self.model.fit(X, Y, 128, 300, callbacks=callbackslist, initial_epoch=startingepoch,shuffle=True)
        pastepochs = list(map(int, [x.replace(".hdf5", "").replace(self.name+"-"+datasetname, "").replace(" ", "") for x in os.listdir("weights") if self.name+"-"+datasetname in x]))
        if max(pastepochs) > 290:
            for filenum in range(1,297):  #delete most of the lower weight files
                try:
                    os.remove("weights/"+self.name+"-"+datasetname+" "+str(filenum)+".hdf5")
                except OSError:
                    pass
        return self.model

class AttentionVGG:
    
    def VGGBlock(self, x, regularizer = None, batchnorm = False):
        if batchnorm:
            x = Conv2D(64, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv1')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(64, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv2')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)

            x = Conv2D(128, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv3')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(128, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv4')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)

            x = Conv2D(256, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv5')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(256, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv6')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(256, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv7')(x)
            x = BatchNormalization()(x)
            local1 = Activation('relu')(x)  # batch*x*y*channel
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool1')(x)

            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv8')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv9')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv10')(x)
            x = BatchNormalization()(x)
            local2 = Activation('relu')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool2')(local2)

            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv11')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv12')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv13')(x)
            x = BatchNormalization()(x)
            local3 = Activation('relu')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool3')(local3)

            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv14')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool4')(x)
            x = Conv2D(512, (3, 3), padding='same', kernel_regularizer=regularizer, name='conv15')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool5')(x)
            x = Flatten(name='pregflatten')(x)
            g = Dense(512, activation='relu', kernel_regularizer=regularizer, name='globalg')(x)  # batch*512
            return (g, local1, local2, local3)
        else:            
            x = Conv2D(64, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv1')(x)
            x = Conv2D(64, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv2')(x)

            x = Conv2D(128, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv3')(x)
            x = Conv2D(128, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv4')(x)

            x = Conv2D(256, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv5')(x)
            x = Conv2D(256, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv6')(x)
            local1 = Conv2D(256, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv7')(x)  # batch*x*y*channel
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool1')(local1)

            x = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv8')(x)
            x = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv9')(x)
            local2 = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv10')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool2')(local2)

            x = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv11')(x)
            x = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv12')(x)
            local3 = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv13')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool3')(local3)

            x = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv14')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool4')(x)
            x = Conv2D(512, (3, 3), activation='relu', padding='same', kernel_regularizer=regularizer, name='conv15')(x)
            x = MaxPooling2D((2, 2), strides=(2, 2), name='pool5')(x)
            x = Flatten(name='pregflatten')(x)
            g = Dense(512, activation='relu', kernel_regularizer=regularizer, name='globalg')(x)  # batch*512
            return (g, local1, local2, local3)

    def __init__(self, att='att3', gmode='concat', compatibilityfunction='pc', datasetname="cifar100", height=32, width=32, channels=3, outputclasses=10, batchnorm=True, batchnormalizeinput=True, weight_decay=0.0005, optimizer=SGD(lr=0.01, momentum=0.9, decay=0.0000001), loss='categorical_crossentropy', metrics=['accuracy']):
        inp = Input(shape=(height, width, channels))
        input = inp
        if batchnormalizeinput:
            input = BatchNormalization()(input)
        regularizer = keras.regularizers.l2(weight_decay)
        self.datasetname = datasetname
        self.outputclasses=outputclasses

        (g, local1, local2, local3) = self.VGGBlock(input,regularizer,batchnorm)

        l1 = Dense(512, kernel_regularizer=regularizer, name='l1connectordense')(local1)  # batch*x*y*512
        c1 = ParametrisedCompatibility(kernel_regularizer=regularizer, name='cpc1')([l1, g])  # batch*x*y
        if compatibilityfunction == 'dp':
            c1 = Lambda(lambda lam: K.squeeze(K.map_fn(lambda xy: K.dot(xy[0], xy[1]), elems=(lam[0], K.expand_dims(lam[1], -1)), dtype='float32'), 3), name='cdp1')([l1, g])  # batch*x*y
        flatc1 = Flatten(name='flatc1')(c1)  # batch*xy
        a1 = Activation('softmax', name='softmax1')(flatc1)  # batch*xy
        reshaped1 = Reshape((-1,512), name='reshape1')(l1)  # batch*xy*512.
        g1 = Lambda(lambda lam: K.squeeze(K.batch_dot(K.expand_dims(lam[0], 1), lam[1]), 1), name='g1')([a1, reshaped1])  # batch*512.

            
        l2 = local2
        c2 = ParametrisedCompatibility(kernel_regularizer=regularizer, name='cpc2')([l2, g])
        if compatibilityfunction == 'dp':
            c2 = Lambda(lambda lam: K.squeeze(K.map_fn(lambda xy: K.dot(xy[0], xy[1]), elems=(lam[0], K.expand_dims(lam[1], -1)), dtype='float32'), 3), name='cdp2')([l2, g])
        flatc2 = Flatten(name='flatc2')(c2)
        a2 = Activation('softmax', name='softmax2')(flatc2)
        reshaped2 =  Reshape((-1,512), name='reshape2')(l2)
        g2 = Lambda(lambda lam: K.squeeze(K.batch_dot(K.expand_dims(lam[0], 1), lam[1]), 1), name='g2')([a2, reshaped2])

        
        l3 = local3
        c3 = ParametrisedCompatibility(kernel_regularizer=regularizer, name='cpc3')([l3, g])
        if compatibilityfunction == 'dp':
            c3 = Lambda(lambda lam: K.squeeze(K.map_fn(lambda xy: K.dot(xy[0], xy[1]), elems=(lam[0], K.expand_dims(lam[1], -1)), dtype='float32'), 3), name='cdp3')([l3, g])
        flatc3 = Flatten(name='flatc3')(c3)
        a3 = Activation('softmax', name='softmax3')(flatc3)
        reshaped3 = Reshape((-1,512), name='reshape3')(l3)
        g3 = Lambda(lambda lam: K.squeeze(K.batch_dot(K.expand_dims(lam[0], 1), lam[1]), 1), name='g3')([a3, reshaped3])
 
        out = ''
        if gmode == 'concat':
            glist = [g3]
            if att == 'att2':
                glist.append(g2)
            if att == 'att3':
                glist.append(g2)
                glist.append(g1)
            predictedG = g3
            if att != 'att1' and att != 'att':
                predictedG = Concatenate(axis=1, name='ConcatG')(glist)
            x = Dense(outputclasses, kernel_regularizer=regularizer, name=str(outputclasses)+'ConcatG')(predictedG)
            out = Activation("softmax", name='concatsoftmaxout')(x)
        else:
            gd3 = Dense(outputclasses, activation='softmax', name=str(outputclasses)+'indepsoftmaxg3')(g3)
            if att == 'att' or att == 'att1':
                out = gd3
            elif att == 'att2':
                gd2 = Dense(outputclasses, activation='softmax', kernel_regularizer=regularizer, name=str(outputclasses)+'indepsoftmaxg2')(g2)
                out = Add(name='addg3g2')([gd3, gd2])
                out = Lambda(lambda lam: lam/2, name='2average')(out)
            else:
                gd2 = Dense(outputclasses, activation='softmax', kernel_regularizer=regularizer, name=str(outputclasses)+'indepsoftmaxg2')(g2)
                gd1 = Dense(outputclasses, activation='softmax', kernel_regularizer=regularizer, name=str(outputclasses)+'indepsoftmaxg2')(g1)
                out = Add(name='addg3g2g1')([gd1, gd2, gd3])
                out = Lambda(lambda lam: lam/3, name='3average')(out)

        model = Model(inputs=inp, outputs=out)
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        name = ("(VGG-"+att+")-"+gmode+"-"+compatibilityfunction).replace('att)', 'att1)')
        print("Generated "+name)
        self.name = name
        self.model = model

    def StandardFit(self, datasetname=None, X=[], Y=[], transfer=False, beep=False, initial_lr=0.01, min_delta=None, patience=7, validation_data=None, lrplateaufactor=None, lrplateaupatience=4):
        Y = keras.utils.to_categorical(Y,self.outputclasses)
        if datasetname==None:
            datasetname=self.datasetname
        if os.path.isfile("weights/"+self.name+"-"+datasetname+" early.hdf5"):
            print("Found early-stopped weights for "+self.name+"-"+datasetname)
            return
        scheduler = LearningRateScaler(25, 0.5, initial_lr)
        startingepoch = 0
        pastepochs = list(map(int, [x.replace(".hdf5", "").replace(self.name+"-"+datasetname, "").replace(" ", "") for x in os.listdir("weights") if (self.name+"-"+datasetname in x) & ("early" not in x)]))
        if len(pastepochs):
            if max(pastepochs) == 300:                
                print("Found completely trained weights for "+self.name+"-"+datasetname)
                return
            self.model.load_weights("weights/"+self.name+"-"+datasetname+" "+str(max(pastepochs))+".hdf5")
            startingepoch = max(pastepochs)
        elif transfer:
            if os.path.isfile("weights/"+self.name+"-"+datasetname+" early.hdf5"):
                self.model.load_weights("weights/"+self.name+"-"+datasetname+" early.hdf5", by_name=True)
            else:
                self.model.load_weights("weights/"+self.name+"-cifar100 300.hdf5", by_name=True)
            scheduler = LearningRateScheduler(transfer_schedule)
        tboardcb = TensorBoard(log_dir='./logs', histogram_freq=0, batch_size=3, write_graph=True, write_grads=False, write_images=False, embeddings_freq=0, embeddings_layer_names=None, embeddings_metadata=None)
        checkpoint = ModelCheckpoint("weights/"+self.name+"-"+datasetname+" {epoch}.hdf5", save_weights_only=True)
        epochprint = LambdaCallback(on_epoch_end=lambda epoch, logs: print("Passed epoch "+str(epoch)))
        callbackslist = [scheduler, checkpoint, epochprint, tboardcb]
        if beep:
            callbackslist.append(Beeper(1))
        if validation_data == None:
            self.model.fit(X, Y, 128, 300, callbacks=callbackslist, initial_epoch=startingepoch,shuffle=True)
        else:
            if min_delta != None:
                callbackslist.append(EarlyStopping(monitor='val_acc', min_delta=min_delta, patience=patience))        
            if lrplateaufactor != None:
                callbackslist.append(ReduceLROnPlateau(monitor='loss', factor = lrplateaufactor, patience = lrplateaupatience))
            self.model.fit(X, Y, 128, 300, callbacks=callbackslist, initial_epoch=startingepoch,shuffle=True,validation_data=(validation_data[0], keras.utils.to_categorical(validation_data[1],self.outputclasses)))            
            self.model.save_weights("weights/"+self.name+"-"+datasetname+" early.hdf5")
        pastepochs = list(map(int, [x.replace(".hdf5", "").replace(self.name+"-"+datasetname, "").replace(" ", "") for x in os.listdir("weights") if (self.name+"-"+datasetname in x) & ("early" not in x)]))
        if max(pastepochs) > 290:
            for filenum in range(1,297):  #delete most of the lower weight files
                try:
                    os.remove("weights/"+self.name+"-"+datasetname+" "+str(filenum)+".hdf5")
                except OSError:
                    pass
        return self.model

    


    def transfer_schedule(epoch):
            if epoch < 30:
                return 0.1
            if epoch < 60:
                return 0.2
            if epoch < 90:
                return 0.4
            if epoch < 120:
                return 0.2
            if epoch < 150:
                return 0.1
            if epoch < 180:
                return 0.05
            if epoch < 210:
                return 0.025
            if epoch < 240:
                return 0.0125
            if epoch < 270:
                return 0.00625
            return 0.003125
    
class AttentionRN:
    def __init__(self, att='att2', gmode='concat', compatibilityfunction='pc', datasetname="cifar10", height=32, width=32, channels=3, outputclasses=100, weight_decay=0.0005, optimizer=SGD(lr=0.01, momentum=0.9), loss='categorical_crossentropy', metrics=['accuracy']):
        inp = Input(shape=(height, width, channels)) #batch*x*y*3
        regularizer = keras.regularizers.l2(weight_decay)
        self.datasetname = datasetname
        self.outputclasses=outputclasses
        x = BatchNormalization()(inp)

        #block1, out batch*(x)*(y)*16
        x = Conv2D(16, (3, 3), padding='same', kernel_regularizer=regularizer, name='block1conv1')(x)
        x = BatchNormalization()(x)
        x = Activation('relu')(x)
        x = Conv2D(16, (3, 3), padding='same', kernel_regularizer=regularizer, name='block1conv2')(x) #batch*x*y*16
        x = BatchNormalization()(x)
        
        #block2, out batch*(x/2)*(y/2)*64
        for i in range(0,18):
            identity = x
            if i == 0:
                identity=Conv2D(64,(2,2), padding='same', kernel_regularizer=regularizer, name='block2dimchangeconv')(identity)
            x = Conv2D(16, (1, 1), padding='same', kernel_regularizer=regularizer, name='block2resblock'+str((i+1))+'conv1')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(16, (3, 3), padding='same', kernel_regularizer=regularizer, name='block2resblock'+str((i+1))+'conv2')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(64, (1, 1), padding='same', kernel_regularizer=regularizer, name='block2resblock'+str((i+1))+'conv3')(x)
            x = BatchNormalization()(x)
            x = Add()([identity,x])
            x = Activation('relu')(x)
        l1 = x #16 filters, 32x32 resolution
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block2pool')(x)

        #block3, out batch*(x/4)*(y/4)*128
        for i in range(0,18):
            identity = x
            if i == 0:
                identity=Conv2D(128, (2,2), padding='same', kernel_regularizer=regularizer, name='block3dimchangeconv')(identity)            
            x = Conv2D(32, (1, 1), padding='same', kernel_regularizer=regularizer, name='block3resblock'+str((i+1))+'conv1')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(32, (3, 3), padding='same', kernel_regularizer=regularizer, name='block3resblock'+str((i+1))+'conv2')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(128, (1, 1), padding='same', kernel_regularizer=regularizer, name='block3resblock'+str((i+1))+'conv3')(x)
            x = BatchNormalization()(x)
            x = Add()([identity,x])
            x = Activation('relu')(x)
        l2 = x #256 filters, 16x16 resolution
        x = MaxPooling2D((2, 2), strides=(2, 2), name='block3pool')(x)

        #block4, out batch*(x/4)*(y/4)*256
        for i in range(0,18):
            identity = x
            if i == 0:
                identity=Conv2D(256, (2,2), padding='same', kernel_regularizer=regularizer, name='block4dimchangeconv')(identity)            
            x = Conv2D(64, (1, 1), padding='same', kernel_regularizer=regularizer, name='block4resblock'+str((i+1))+'conv1')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(64, (3, 3), padding='same', kernel_regularizer=regularizer, name='block4resblock'+str((i+1))+'conv2')(x)
            x = BatchNormalization()(x)
            x = Activation('relu')(x)
            x = Conv2D(256, (1, 1), padding='same', kernel_regularizer=regularizer, name='block4resblock'+str((i+1))+'conv3')(x)
            x = BatchNormalization()(x)
            x = Add()([identity,x])
            x = Activation('relu')(x)
        l3 = x #512 filters, 8x8 resolution
        
        x = Conv2D(256, (3, 3), padding='same', kernel_regularizer=regularizer, name='outconv')(x) 
        x = BatchNormalization()(x)
        x = MaxPooling2D((2,2), strides=(2,2), name="gpool")(x)
        gbase = Flatten(name='pregflatten')(x)
        
        g64 = Dense(64, kernel_regularizer=regularizer, name='globalg64')(gbase)
        g128 = Dense(128, kernel_regularizer=regularizer, name='globalg128')(gbase)
        g256 = Dense(256, kernel_regularizer=regularizer, name='globalg256')(gbase)        


        c1 = ParametrisedCompatibility(kernel_regularizer=regularizer, name='cpc1')([l1, g64])  # batch*x*y
        if compatibilityfunction == 'dp':
            c1 = Lambda(lambda lam: K.squeeze(K.map_fn(lambda xy: K.dot(xy[0], xy[1]), elems=(lam[0], K.expand_dims(lam[1], -1)), dtype='float32'), 3), name='cdp1')([l1, g64])  # batch*x*y
        flatc1 = Flatten(name='flatc1')(c1)  # batch*xy
        a1 = Activation('softmax', name='softmax1')(flatc1)  # batch*xy
        reshaped1 = Reshape((-1,64), name='reshape1')(l1)  # batch*xy*256.
        g1 = Lambda(lambda lam: K.squeeze(K.batch_dot(K.expand_dims(lam[0], 1), lam[1]), 1), name='g1')([a1, reshaped1])  # batch*256.
        
        c2 = ParametrisedCompatibility(kernel_regularizer=regularizer, name='cpc2')([l2, g128])
        if compatibilityfunction == 'dp':
            c2 = Lambda(lambda lam: K.squeeze(K.map_fn(lambda xy: K.dot(xy[0], xy[1]), elems=(lam[0], K.expand_dims(lam[1], -1)), dtype='float32'), 3), name='cdp2')([l2, g128])
        flatc2 = Flatten(name='flatc2')(c2)
        a2 = Activation('softmax', name='softmax2')(flatc2)
        reshaped2 =  Reshape((-1,128), name='reshape2')(l2)
        g2 = Lambda(lambda lam: K.squeeze(K.batch_dot(K.expand_dims(lam[0], 1), lam[1]), 1), name='g2')([a2, reshaped2])

        c3 = ParametrisedCompatibility(kernel_regularizer=regularizer, name='cpc3')([l3, g256])
        if compatibilityfunction == 'dp':
            c3 = Lambda(lambda lam: K.squeeze(K.map_fn(lambda xy: K.dot(xy[0], xy[1]), elems=(lam[0], K.expand_dims(lam[1], -1)), dtype='float32'), 3), name='cdp3')([l3, g256])
        flatc3 = Flatten(name='flatc3')(c3)
        a3 = Activation('softmax', name='softmax3')(flatc3)
        reshaped3 = Reshape((-1,256), name='reshape3')(l3)
        g3 = Lambda(lambda lam: K.squeeze(K.batch_dot(K.expand_dims(lam[0], 1), lam[1]), 1), name='g3')([a3, reshaped3])

        out = ''
        if gmode == 'concat':
            glist = [g3]
            if att == 'att2':
                glist.append(g2)
            if att == 'att3':
                glist.append(g2)
                glist.append(g1)
            predictedG = g3
            if att != 'att1' and att != 'att':
                predictedG = Concatenate(axis=1, name='ConcatG')(glist)
            x = Dense(outputclasses, kernel_regularizer=regularizer, name=str(outputclasses)+'ConcatG')(predictedG)
            out = Activation("softmax", name='concatsoftmaxout')(x)
            
        else:
            gd3 = Dense(outputclasses, activation='softmax', name=str(outputclasses)+'indepsoftmaxg3')(g3)
            if att == 'att' or att == 'att1':
                out = gd3
            elif att == 'att2':
                gd2 = Dense(outputclasses, activation='softmax', kernel_regularizer=regularizer, name=str(outputclasses)+'indepsoftmaxg2')(g2)
                out = Add(name='addg3g2')([gd3, gd2])
                out = Lambda(lambda lam: lam/2, name='2average')(out)
            else:
                gd2 = Dense(outputclasses, activation='softmax', kernel_regularizer=regularizer, name=str(outputclasses)+'indepsoftmaxg2')(g2)
                gd1 = Dense(outputclasses, activation='softmax', kernel_regularizer=regularizer, name=str(outputclasses)+'indepsoftmaxg2')(g1)
                out = Add(name='addg3g2g1')([gd1, gd2, gd3])
                out = Lambda(lambda lam: lam/3, name='3average')(out)

        model = Model(inputs=inp, outputs=out)
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        name = ("(RN-"+att+")-"+gmode+"-"+compatibilityfunction).replace('att)', 'att1)')
        print("Generated "+name)
        self.name = name
        self.model = model
    
    def StandardFit(self, datasetname=None, X=[], Y=[], beep=False, initial_lr=0.01, min_delta=None, patience=3, validation_data=None, lrplateaufactor=None, lrplateaupatience=4):
        Y = keras.utils.to_categorical(Y,self.outputclasses)
        if datasetname==None:
            datasetname=self.datasetname
        if os.path.isfile("weights/"+self.name+"-"+datasetname+" early.hdf5"):
            print("Found early-stopped weights for "+self.name+"-"+datasetname)
            return
        scheduler = LearningRateScaler([60, 120, 160], 0.2, initial_lr)
        startingepoch = 0
        pastepochs = list(map(int, [x.replace(".hdf5", "").replace(self.name+"-"+datasetname, "").replace(" ", "") for x in os.listdir("weights") if (self.name+"-"+datasetname in x) & ("early" not in x)]))
        if pastepochs:
            if max(pastepochs) == 200:
                print("Found completely trained weights for "+self.name+"-"+datasetname)
                return
            self.model.load_weights("weights/"+self.name+"-"+datasetname+" "+str(max(pastepochs))+".hdf5")
            startingepoch = max(pastepochs)
        tboardcb = TensorBoard(log_dir='./logs', histogram_freq=0, batch_size=3, write_graph=True, write_grads=False, write_images=False, embeddings_freq=0, embeddings_layer_names=None, embeddings_metadata=None)
        checkpoint = ModelCheckpoint("weights/"+self.name+"-"+datasetname+" {epoch}.hdf5", save_weights_only=True)
        epochprint = LambdaCallback(on_epoch_end=lambda epoch, logs: print("Passed epoch "+str(epoch)))
        callbackslist = [scheduler, checkpoint, epochprint, tboardcb]
        if beep:
            callbackslist.append(Beeper(1))
        if validation_data == None:
            self.model.fit(X, Y, 64, 200, callbacks=callbackslist, initial_epoch=startingepoch,shuffle=True)
        else:
            if min_delta != None:
                callbackslist.append(EarlyStopping(monitor='val_acc', min_delta=min_delta, patience=patience))
            if lrplateaufactor != None:
                callbackslist.append(ReduceLROnPlateau(monitor='acc', factor = lrplateaufactor, patience = lrplateaupatience))
            self.model.fit(X, Y, 64, 200, callbacks=callbackslist, initial_epoch=startingepoch,shuffle=True,validation_data=(validation_data[0], keras.utils.to_categorical(validation_data[1],self.outputclasses)))    
            self.model.save_weights("weights/"+self.name+"-"+datasetname+" early.hdf5")
        pastepochs = list(map(int, [x.replace(".hdf5", "").replace(self.name+"-"+datasetname, "").replace(" ", "") for x in os.listdir("weights") if (self.name+"-"+datasetname in x) & ("early" not in x)]))
        if max(pastepochs) > 190:
            for filenum in range(1,197):
                try:
                    os.remove("weights/"+self.name+"-"+datasetname+" "+str(filenum)+".hdf5")
                except OSError:
                    pass
        return self.model
        

class ParametrisedCompatibility(Layer):

    def __init__(self, kernel_regularizer=None, **kwargs):
        super(ParametrisedCompatibility, self).__init__(**kwargs)
        self.regularizer = kernel_regularizer

    def build(self, input_shape):
        self.u = self.add_weight(name='u', shape=(input_shape[0][3], 1), initializer='uniform', regularizer=self.regularizer, trainable=True)
        super(ParametrisedCompatibility, self).build(input_shape)

    def call(self, x):  # add l and g. Dot the sum with u.
        return K.dot(K.map_fn(lambda lam: (lam[0]+lam[1]),elems=(x),dtype='float32'), self.u)

    def compute_output_shape(self, input_shape):
        return (input_shape[0][0], input_shape[0][1], input_shape[0][2])


class LearningRateScaler(Callback):
    
    def __init__(self, epochs, multiplier, initial_lr=None):
        self.multiplier = multiplier
        self.epochs = epochs
        self.initial_lr = initial_lr
        self.startingepoch = True
    
    def on_train_begin(self, logs=None):
        if self.initial_lr == None:
            self.initial_lr = K.get_value(self.model.optimizer.lr)
        print("Initial lr="+str(self.initial_lr))

    def on_epoch_begin(self, epoch, logs=None):
        if not hasattr(self.model.optimizer, 'lr'):
            raise ValueError('Optimizer must have a "lr" attribute.')
        print("Current lr: " + str(K.get_value(self.model.optimizer.lr)))
        lr = self.initial_lr
        if (epoch > 0 and epoch % self.epochs == 0) or self.startingepoch:
            for i in range(0, epoch // self.epochs):
                lr = lr * self.multiplier
            K.set_value(self.model.optimizer.lr, lr)
            print("Updated learning rate to "+str(lr))
            self.startingepoch = False
        elif isinstance(self.epochs, list):
            if epoch>0 and epoch in self.epochs.sort():
                for i in range(0, self.epochs.sort().index(epoch)+1):
                    lr = lr * self.multiplier
                K.set_value(self.model.optimizer.lr, lr)
                print("Updated learning rate to "+str(lr))    
        
    
    def on_epoch_end(self, epoch, logs=None):
        startingepoch = False
    
        


class Beeper(Callback):

    def __init__(self, batches):
        self.batches = batches
    
    def on_batch_end(self, batch, logs={}):
        if batch > 0 and batch % self.batches == 0:
            winsound.Beep(440,150)


if __name__ == "__main__":
    testmodel = StandardVGG()