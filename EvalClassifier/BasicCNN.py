import numpy as np

BATCH_SIZE = 32
EPOCHS = 128
NUM_CLASS = 2


class BasicCNN:

    def __init__(self):
        from EvalClassifier.extract_bytes_io import extract_bytes
        self.gan_data = extract_bytes('data/gan_01.0hr.csv', is_fake=True)
        self.real_data = extract_bytes('data/real_01.5hr.csv', is_fake=False)
        self.straw_data = extract_bytes('data/straw_01.0hr.csv', is_fake=True)

    @staticmethod
    def _gen_model():
        from EvalClassifier.extract_bytes_io import WINDOW_SIZE
        data_shape = [2, WINDOW_SIZE, 1]

        from keras.models import Sequential
        from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense

        model = Sequential()
        model.add(Conv2D(
            filters=8,
            kernel_size=(3, 3),
            strides=(1, 1),
            padding='same',
            activation='relu',
            kernel_initializer='random_uniform',
            input_shape=data_shape,
        ))
        model.add(Conv2D(
            filters=16,
            kernel_size=(3, 3),
            strides=(1, 1),
            padding='same',
            activation='relu',
            kernel_initializer='random_uniform',
        ))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Flatten())
        model.add(Dense(16, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(NUM_CLASS, activation='softmax'))

        model.compile(
            loss='categorical_crossentropy',
            optimizer='rmsprop',
            metrics=['accuracy'],
        )

        return model

    @staticmethod
    def _show_confusion_matrix(target_class_name, predictions, labels):
        import tensorflow as tf
        import pandas as pd

        confusion = tf.math.confusion_matrix(
            labels=labels,
            predictions=predictions,
            num_classes=NUM_CLASS,
        ).numpy()

        normal_confusion = np.around(confusion.astype('float') / confusion.sum(axis=1)[:, np.newaxis], decimals=4)
        normal_confusion_df = pd.DataFrame(normal_confusion, index=['real', 'fake'], columns=['real', 'fake'])

        from matplotlib import pyplot as plt
        import seaborn as sns
        figure = plt.figure(figsize=(4, 4))
        sns.heatmap(normal_confusion_df, annot=True, cmap=plt.get_cmap('Blues'), fmt='.2%')
        plt.title('CNN {} Classifier Confusion Matrix'.format(target_class_name))
        plt.ylabel('True Labels')
        plt.xlabel('Predicted Labels')
        plt.tight_layout()
        plt.show()

    def _train_and_test(self, target_class_name, samples, labels):
        from sklearn.model_selection import train_test_split
        from keras.utils import to_categorical

        model = self._gen_model()

        x_train, x_test, y_train, y_test = train_test_split(samples, labels, test_size=0.3)  # , random_state=43234)

        y_test_original = y_test.copy()

        x_train = np.expand_dims(x_train, axis=-1)
        y_train = to_categorical(y_train, num_classes=NUM_CLASS)
        x_test = np.expand_dims(x_test, axis=-1)
        y_test = to_categorical(y_test, num_classes=NUM_CLASS)

        model.fit(
            x=x_train,
            y=y_train,
            batch_size=BATCH_SIZE,
            epochs=EPOCHS,
            validation_data=(x_test, y_test),
            shuffle=True,
            verbose=2,
        )

        label_predictions = model.predict_classes(x_test)
        self._show_confusion_matrix(target_class_name, label_predictions, y_test_original)

    def train_straw(self):
        samples = np.concatenate((self.straw_data[0], self.real_data[0]))
        labels = np.concatenate((self.straw_data[1], self.real_data[1]))

        self._train_and_test('Strawman', samples, labels)

    def train_voiceover(self):
        samples = np.concatenate((self.gan_data[0], self.real_data[0]))
        labels = np.concatenate((self.gan_data[1], self.real_data[1]))

        self._train_and_test('Voiceover', samples, labels)