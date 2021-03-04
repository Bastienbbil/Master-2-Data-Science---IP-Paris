import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.pipeline import Pipeline

def meta_extract(data):
    return pd.DataFrame({
        "trial":  [data[index].trial_code for index in range(len(data))],
        "age": [data[index].age for index in range(len(data))],
        "gender": [data[index].gender for index in range(len(data))],
        "height": [data[index].height for index in range(len(data))],
        "weight": [data[index].weight for index in range(len(data))],
        "bmi": [data[index].bmi for index in range(len(data))],
        "laterality": [data[index].laterality for index in range(len(data))],
        "sensor": [data[index].sensor for index in range(len(data))],
        "pathology": [data[index].pathology_group for index in range(len(data))],
        "is_control": [data[index].is_control for index in range(len(data))],
        "foot": [data[index].foot for index in range(len(data))]
        })

def data_into_pandas_train(data, labels):
    signal = pd.DataFrame(columns=['AV', 'AX', 'AY', 'AZ', 'RV', 'RX', 'RY', 'RZ'])
    steps = pd.DataFrame(columns=['step'])
    nb_steps =[]
    for index in range(len(data)):
        nb_steps.append(len(data[index].signal))
        signal = pd.concat([signal, data[index].signal]) 
        step = np.zeros(len(data[index].signal))
        for i in labels[index]:
            step[i[0]:i[1]+1] = 1
        step = pd.DataFrame(step, columns=['step'])
        steps = pd.concat([steps,step])
    steps = steps.reset_index(drop=True)
    signal = signal.reset_index(drop=True)
    return steps, signal, nb_steps

def data_into_pandas_test(data):
    signal = pd.DataFrame(columns=['AV', 'AX', 'AY', 'AZ', 'RV', 'RX', 'RY', 'RZ'])
    nb_steps =[]
    for index in range(len(data)):
        nb_steps.append(len(data[index].signal))
        signal = pd.concat([signal, data[index].signal]) 
    signal = signal.reset_index(drop=True)
    return signal, nb_steps

def pred_into_format(steps_pandas, size_trials):
    n = 0
    steps = []
    for i in size_trials:
        steps.append(steps_pandas[n:n+i].reset_index(drop=True))
        n = n + i
    list =[]
    for index in range(len(steps)):
        a = np.where(np.diff(steps[index]['step']) == 1)
        b = np.where(np.diff(steps[index]['step']) == -1)
        labels = [[a[0][i]+1, b[0][i]] for i in range(min(len(a[0]), len(b[0])))]
        list.append(labels)
    lab = np.array(list)
    return lab

def treshold(labels):
    diff = []
    for index in range(len(labels)):
        diff.append(min(np.diff(labels[index],axis=1))[0])
    treshold = min(diff)
    return treshold

def keep_step(lab,treshold):
    list = []
    for index in range(len(lab)):
        check = np.diff(lab[index],axis=1) >= treshold
        liste = []
        for i in range(len(lab[index])):
            if check[i][0] == True:
                liste.append(lab[index][i])
        list.append(liste)
    pred = np.array(list)
    return pred


class Detector():
    def __init__(self, threshold=0.5, order=40):
        self.threshold = threshold
        self.order = order
        self.step_template = None

    def fit(self, X, y):
        self.model = RFC(n_estimators=10)
        assert len(X) == len(
            y), f"Wrong dimensions (len(X): {len(X)}, len(y): {len(y)})."
        data_train, labels_train = X, y
        steps_train, signal_train, size_trials_train = data_into_pandas_train(data_train, labels_train)
        self.treshold = treshold(labels_train) 
        self.model.fit(signal_train,steps_train.values.ravel())
        return self

    def predict(self, X):
        signal_test, size_trials_test = data_into_pandas_test(X)
        steps_predicted = self.model.predict(signal_test)
        steps_p = pd.DataFrame(steps_predicted, columns=['step'])
        steps_ = pred_into_format(steps_p, size_trials_test)
        pred = keep_step(steps_,self.treshold)
        return pred


def get_estimator():
    # step detection
    detector = Detector()

    # make pipeline
    pipeline = Pipeline(steps=[('detector', detector)])

    return pipeline