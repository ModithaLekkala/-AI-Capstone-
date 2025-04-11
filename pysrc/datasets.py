from torch.utils.data import Dataset
import kagglehub

class UNSW_NB15_Dataset(Dataset):
    def __init__(self, X, Y):
        self.X = X
        self.Y = Y

    def __len__(self):
        return len(self.Y)
    
    def __getitem__(self, index):
        sample = self.X[index]
        label = self.Y[index]
        return sample, label
    
    def get_labels(self):
        return self.Y