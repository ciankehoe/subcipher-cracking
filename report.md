# CA216 Operating Systems: "Cracking the Substitution Cipher" Report

### How and why you chose the method you did to solve this problem:
----
When I first began researching cryptographic deciphering methods / cryptanalysis, I immediately came across the standard methods of frequency analysis, coupled with the use of various ngrams, ngraphs, common N-letter words, etc.
I began to experiment and model solutions around these alone, but very quickly found that it would require a high degree of deep 'manual' analysis of any given text in order to create any sort of reliable, efficient or automated system through which I would design my solution. At this stage, I was still working purely on an entirely linear approach, while still trying to understand the problem space.

I instead started searching for a more algorithmically sound method. I wanted to avoid the verbose and brutish statistical dismantling of the text, and look for a more elegant and concise approach.

I soon came across Simulated Annealing (SA) and hill climbing techniques. With some past experience with optmization algorithms such as gradient descent, this provided the logical and 'visual' representation of a solution that seemed perfect to me for the task.

I mentioned hill climbing, a technique with the aim of continually moving 'upwards', increasing our score. The key difference with Simulated Annealing is allowing us to accept scores that are less than the current max. The randomness brought in during the thousands of trials allows for us to explore the possibilites of a decreasing score which may then in turn lead to an unfounded 'route' to a higher score. So by changing the key negatively, it opens up the possibility of going down in order go up again but higher. Like taking 1 step back in order to go 3 steps forward. 

My initial approach at applying the relevant techniques was by implementing the general case in a way that suited the cipher. It was a single threaded implementation and proved to be very effective. Through the use of logarithmic probability (which proved challenging to implement) and quadgrams alone, I had found a very flexible system which proved well capable of finding the correct key almost every time in a reasonable time. I decided to continue with this method due to how clean and concise it was for how positive a result it gave. 

This first round, effectively, ended up being very close to my final solution in that it follows the same set of principles (as is well defined and commented in my code) but obviously without being parallellized.

This was my next step. Simulated Annealing is inherently sequential so it proved difficult to do without compromising the integrity of the core algorithm. There's not much that can be segmented into seperate processes as each section relies on the success/result of the previous. I'll discuss in more detail why I decided on my final multiprocessed approach below, in **Testing**.

----

*Some resources I used regarding the SA / Hill Climbing:*
1. https://www.sciencedirect.com/science/article/abs/pii/0167278990900843
1. https://uk.mathworks.com/help/gads/how-simulated-annealing-works.html
1. https://ieeexplore.ieee.org/document/25760
1. http://rbanchs.com/documents/THFEL_PR15.pdf
1. http://katrinaeg.com/simulated-annealing.html

### Testing
----
I essentially had **4 different primary stages/versions** to the development and phased testing of the project.

**1. Initial Linear Solution:**
This was my fastest solution in the end, but did not feature any parallel techniques. It provided an average time of 26.538 seconds on the os-sub-cipher.txt file provided on Loop. I tested it using primarily the time library, as well as by tweaking several of the parameters involved, including the number of trials, starting keys, how many iterations to allow without improvement, and by implementing suitable stopping / exit criteria. 

The exit criteria which proved particularly effective were:
- **Presence of dictionary words (check_english_dic()):**
Meant that statistically we were able to exit the process right when a very strong solution had been found. This may vary with edge cases where we have an unusual number (low) of unique words in the text.
- **The number_iterations_without_improvements** i.e random restarts.
- **Manual termination.**
Allowing the program to run until interrupted by the user. Not ideal for distributed use, but effective when eyeballing text and approximating how well it's performing. Can tell when restarts are required and maximas have been hit.



**2. Multiproccesing : shared global max score**
At first I thought this would be a useful way of approaching the parallelization of the system. Basically everytime a new maxscore was found, a global maxscore variable was set, and this became the key / score which is then used as the parent key for all following iterations (until each process diverges again.) Essentially the idea was to converge the individual solutions on high scores to allow for better growth/increase. But this did not prove to make any significant changes to the timing at all. I believe this result was due to the fact that really no marked increase would take place because by doing this I would be putting them back on the same track, meaning it would defeat the purpose of allowing us to explore worse solutions in order to find better ones.

**3. First process to meet exit criteria:**
I tried to implement a case where we would run/start all processes and once one of them meets the exit_criteria, we would exit with the key generated by that particular process. Thus meaning that because we have multiple workers exploring different 'routes' (taking a hill climbing analogy) with different keys, we would then get the quickest result out of the 5 of them. 

As this would be true parallellized, it would mean we are essentially upping the probability of obtaining an optimal solution in optimal time. It's like sending multiple people up a mountain. Between 5 or 10 people, they'll explore and find the quickest route much more efficiently and quickly than a single person would. 

However, this proved very difficult to get working correctly due to the nature of trying to have one exit condition then terminate all processes in the correct way. This is definitely one thing I would like to try again. This ended up being rather close to my final solution.


**4. Final Solution:**
When single threaded / linear, I had to keep the exit criteria of *number_iterations_without_improvement* (how many random restarts we do) somewhat high so that the single threaded program did not 'give up too soon' and insufficiently explore the sample/solution space. At the same time, I could not keep it too high, as this ties into the running time of the program, and if it does get stuck at a local maximum, we could be waiting a while.

But, by implementing multi-processing, I was able to reduce this as we had multiple workers to explore more solutions in the same time. However, in the end, my final solution did not utilize the exit criteria to their full extent as all the processes had to finish. Instead, it allows all the processes to finish and then cherry picks the optimal/best solution found by all the processes (from the shared list) and uses that.

Taking the hill climbing analogy, it would be like exploring *CPU_COUNT* times as many routes. It ended up with an average best running time performance of 41 seconds on the same file from Loop. Although it increased the running time, it was worthwhile, as it consistently found the correct key. It increased it's reliability.

----

### What would you do differently were you to undertake this exercise again?

- Consider diving further into the analysis of the text in order to compliment my existing approach. With more informed decisions it may allow me to improve and optimize the algorithms performance when it comes to swapping keys and calculating the value of the keys, and the deciphered text while deciphering.

    For example, use the actual *<insert language here>* [English] dictionary itself more. Check the words in the deciphered text against words in it. If a word is in both, raise the rank of that word's letters, thus calcualting a score based on word and letter scores.

- Attempt better parallelization using message passing and explore other possibilites.
