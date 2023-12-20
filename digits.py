import os
import numpy as np
import keras
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D
import matplotlib.pyplot as plt
from collections import namedtuple


# class to train and test a NN to classify handwritten digits 0-9
class MNISTDigit:

    # setup
    def __init__(self, new_model=False, use_black_and_white_data=False, force_load=False):
        self.model = None
        self.model_fn = "digit_nn_model.keras"
        self.history = None
        self.use_black_and_white_data = use_black_and_white_data
        self.force_load = force_load
        self.get_digit_data()
        self.get_model(new_model=new_model)

    # get mnist digit data from keras
    def get_digit_data(self):
        # mnist digit data
        (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()
        x_train = x_train / 255
        y_train = to_categorical(y_train, 10)
        x_test = x_test / 255
        y_test = to_categorical(y_test, 10)
        # Split train data into training and validation
        x_validation = x_train[-10000:]
        y_validation = y_train[-10000:]
        x_train = x_train[:-10000]
        y_train = y_train[:-10000]
        # modify data if self.use_black_and_white_data is True
        if self.use_black_and_white_data is True:
            for x in [x_train, x_validation, x_test]:
                x[x >= 0.5] = 1.0
                x[x < 0.5] = 0.0
        # return named tuple
        digitDataResult = namedtuple("digitDataResult", [
            "x_train",
            "y_train",
            "x_validation",
            "y_validation",
            "x_test",
            "y_test",
        ])
        self.digit_data = digitDataResult(
            x_train=x_train,
            y_train=y_train,
            x_validation=x_validation,
            y_validation=y_validation,
            x_test=x_test,
            y_test=y_test,
        )

    # init or load model
    def get_model(self, new_model=False):
        if self.force_load is True:
            if new_model is True:
                raise AssertionError("self.force_load and new_model cannot both be True")
        if (self.force_load is True) or (os.path.exists(self.model_fn) and new_model is False):
            self.model = keras.models.load_model(self.model_fn)
        else:
            self.init_model()
            keras.models.save_model(self.model, self.model_fn)

    # specify NN structure and compilation
    def init_model(self):
        # model
        self.model = Sequential()
        self.model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1)))
        self.model.add(Conv2D(64, kernel_size=(3, 3), activation='relu', input_shape=(28, 28, 1)))
        self.model.add(MaxPooling2D(pool_size=(2, 2)))
        self.model.add(Dropout(0.25))
        self.model.add(Flatten())
        self.model.add(Dense(128, activation="relu"))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(10, activation="softmax"))
        # training configuration
        self.model.compile(
            # Optimizer
            optimizer='adam',  # keras.optimizers.legacy.RMSprop(),  # keras.optimizers.RMSprop(),
            # Loss function to minimize
            loss='categorical_crossentropy',  # keras.losses.SparseCategoricalCrossentropy(),
            # List of metrics to monitor
            metrics=['accuracy'],  # [keras.metrics.SparseCategoricalAccuracy()],
        )

    # run training on model
    def train_model(self):
        self.get_digit_data()
        # run training
        self.history = self.model.fit(
            x=self.digit_data.x_train,
            y=self.digit_data.y_train,
            batch_size=128,
            epochs=5,
            validation_data=(self.digit_data.x_validation, self.digit_data.y_validation),
        )
        # save model
        keras.models.save_model(self.model, self.model_fn)

    # run N predictions  with model on input of shape (N, 28, 28)
    def predict(self, input):
        predictions = self.model.predict(input)
        return np.argmax(predictions, axis=1)


if __name__ == "__main__":
    # init
    mnd = MNISTDigit(
        new_model=False,
        use_black_and_white_data=True,
    )

    # # train (comment/uncomment as needed)
    # mnd.train_model()

    # visualize predictions
    x_test = mnd.digit_data.x_validation[:10]
    y_test = mnd.digit_data.y_validation[:10]
    y_predict = mnd.predict(input=x_test)
    for x, y, yp in zip(x_test, y_test, y_predict):
        y = np.argmax(y)
        plt.imshow(x)
        plt.title(f"actual: {y} | predicted: {yp}")
        plt.show()

    # test
    validation_predictions = mnd.predict(input=mnd.digit_data.x_validation)
    y_validation = np.argmax(mnd.digit_data.y_validation, axis=1)
    validation_accuracy = np.sum(y_validation == validation_predictions) / validation_predictions.shape[0]
    print(f"Validation Accuracy: {validation_accuracy}")
