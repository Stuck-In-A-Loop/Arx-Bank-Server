import pickle


def load_init_face_data():
    with open("face_encodings.pkl", "rb") as f:
        data = pickle.load(f)
        name_encodings_map = {}
        for i in range(len(data["names"])):
            name_encodings_map[data["names"][i]] = data["encodings"][i]
        return name_encodings_map