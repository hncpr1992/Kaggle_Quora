# Kaggle_Quora

The Quora Question Pairs Kaggle competition requires the kagglers to give accurate evaluation on whether the two <br>
queries as a pair refer to the same topic of questions or not.

There are two general ways to approach these problems: <br>
1. Build handcraft features from the text and model them with xgboost and ensemble.<br>
2. Embed the text to distributed representation vectors and develop deep learning model (RNN or CNN) and ensemble <br>

During this competition, I first tried the method 1, which gives me results within 0.33 to 0.35. Then, I get away and
embark on learning some deep learning methods and get back. I start to build Siamese Recurrent Architecture and make some
change on it. Then, after the finish of this competition, I also implement a CNN architecture proposed by other kagglers,
which gives a great improvement on the accuracy.<br>

Most kagglers are using a kind of magic features which will improve the accuracy a lot <br>

Reference: <br>
<a href="https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=5&ved=0ahUKEwickJT52c_UAhVJ2IMKHdRXCuYQFgg6MAQ&url=https%3A%2F%2Fwww.cs.cmu.edu%2F~rsalakhu%2Fpapers%2Foneshot1.pdf&usg=AFQjCNEFB93X4PyZIriYa-iee1lL7250gQ&sig2=AExXqidnx0TpFyO1lb8dPA">Learning Sentence Similarity with Siamese Recurrent Architectures</a><br>
https://engineering.quora.com/Semantic-Question-Matching-with-Deep-Learning <br>
http://www.wildml.com/2015/12/implementing-a-cnn-for-text-classification-in-tensorflow/<br>
https://www.kaggle.com/rethfro/1d-cnn-single-model-score-0-14-0-16-or-0-23<br>

Final Rank:  <br>
660/3307 (Top 20%) with LSTM. This rank is on the leader board <br>
https://github.com/hncpr1992/Kaggle_Quora/blob/master/code/RNN_Keras.ipynb<br>
552/3307 (Top 16%) with CNN. This rank is not on leader board because it is submitted after the deadline of the competition.<br>
https://github.com/hncpr1992/Kaggle_Quora/blob/master/code/CNN_Keras.py<br>

Both codes include ideas from other kagglers. I learned a lot.

Private Leader Board 660<br>
https://www.kaggle.com/c/quora-question-pairs/leaderboard
