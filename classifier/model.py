import torch
import torch.nn as nn
import pickle

import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import re

max_length = 100
batch_size = 2
embedding_dim = 50
hidden_dim = 64
n_layers = 1
bidirectional = True
dropout = 0.5
epochs = 10

class TextClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, output_dim,
                 n_layers=1, bidirectional=True, dropout=0.5):
        super(TextClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers=n_layers,
                            bidirectional=bidirectional, batch_first=True,
                            dropout=dropout if n_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.attention = nn.Linear(hidden_dim * (2 if bidirectional else 1), 1)
        self.fc = nn.Linear(hidden_dim * (2 if bidirectional else 1), output_dim)

    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(embedded)

        attn_scores = self.attention(lstm_out)
        attn_weights = torch.softmax(attn_scores, dim=1)

        weighted = torch.sum(attn_weights * lstm_out, dim=1)
        out = self.dropout(weighted)
        logits = self.fc(out)
        return logits

def encode_sentence(sentence, vocab, max_length=100):
    tokens = sentence.split()
    token_indices = [vocab.get(token, vocab["<unk>"]) for token in tokens]
    if len(token_indices) < max_length:
        token_indices += [vocab["<pad>"]] * (max_length - len(token_indices))
    else:
        token_indices = token_indices[:max_length]
    return torch.tensor(token_indices, dtype=torch.long).unsqueeze(0)
