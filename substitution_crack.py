import random
import string
import time
import sys
import os
from math import log10
from multiprocessing import Process
import multiprocessing
from operator import itemgetter

class ngram_statistics(object):
    """Loads in a file as an object and allow us to analyse it and calculate the relevant log probabilites
       Mathematical method which I provide reference to in report.
    """
    def __init__(self,ngramfile):

        self.ngrams = {}

        for line in open(ngramfile):
            ngram, count = line.split(' ')
            self.ngrams[ngram] = int(count)

        self.ngram_length = len(ngram)
        self.N = sum(self.ngrams.values())

        for ngram in list(self.ngrams.keys()):
            # calculating log probability --> fitness
            # Returns the base 10 log of each ngrams count occurence, dividded by N
            self.ngrams[ngram] = log10(float(self.ngrams[ngram])/self.N)

        self.floor = log10(0.01/self.N)

    def get_fitness_score(self, deci_text):
        """Calculate the fitness score of a piece of text"""
        score = 0

        ngrams = self.ngrams.__getitem__

        for i in range(len(deci_text) - self.ngram_length + 1):
            if deci_text[i:i + self.ngram_length] in self.ngrams:
                score += ngrams(deci_text[i:i+self.ngram_length])
            else:
                score += self.floor

        return score

# instantiate our quadgram statistics for fitness rating
quadfitness = ngram_statistics('english_quadgrams.txt')
# instantiate our trigram statistics for fitness rating
trifitness = ngram_statistics('english_trigrams.txt')
# instantiate our bigram statistics for fitness rating
bifitness = ngram_statistics('english_bigrams.txt')

# load in language dictionary (of choice) for checking against deciphered text
# Allows us to use check for the presence of actual words in our deciphered
# text and use that as exit criteria.
english_dictionary = set(line.strip().upper() for line in open('web2.txt'))

# Initialize a started SyncManager object.
# This allows us to share an object between processes.
manager = multiprocessing.Manager()
# Our shared object will be a list.
final_scores = manager.list()

def create_key(key):
    """Helper function used to map our generated solution key characters to the equivalent letters.
       Especially helpful for outputting our key-file in the required format.
    """
    alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # Initialise dictionary for key:value mapping
    key_mapping = {}

    # Loop to map our key to the correct dictionary order
    # E.g / A = 1st Key Letter, B = 2nd Key Letter, etc.
    i = 0
    while i < len(key):
        key_mapping[key[i]] = alphabet[i]
        i += 1
    
    return key_mapping

def decipher_text(ciphertext, key):
    """Function to take some ciphertext and some key and return the
       deciphered version of the text using that key.
    """

    # Remove all unnecessary punctuation from ciphered text.
    # Makes the text easier to parse and analyse. 
    ciphertext = ciphertext.translate(str.maketrans('', '', string.punctuation))

    # I specifically removed these two special double quotes as they were present in
    # the os-sub-cipher.txt sample file and aren't targeted by string.punctuation. 
    ciphertext = ciphertext.replace('”', '')
    ciphertext = ciphertext.replace('“', '')
    
    # Initialize our output of deciphered text as an empty string.
    result = ""
    
    # Utilize the create_key() method to create our dictionary mapping
    # for easy deciphering.
    key_mapping = create_key(key)
    
    # Simple loop which goes to the encrypted ciphertext and
    # using the key_mapping, decrypts the text using our key (dictionary).
    for char in ciphertext:
        # We do not want to try and translate / decrypt any characters using the key_mapping that are
        # not in our key. This check takes care of special cases as well as integers, etc.
        if char not in key_mapping:
            result = result + char
        # Once the character in the ciphertext valid, we replace it with the corresponding
        # character from our current key.
        else:
            result = result + key_mapping[char]

    return result

def check_english_dic(decipheredtext, dictionary):
    """ This function is implemented to check for exit criteria. It takes our loaded english dictionary 
        and checks the deciphered text for words valid english dictionary words. This means that once a certain number, or all
        of the words in the deciphered text are valid words, we can exit. In my opinion, we can and must exit without knowing all words
        are in our loaded dictionary. This is because some valid words may not be present in the dictionary, such as specific names or terms.
    """
    # Create a set of words for the currently deciphered text.
    # This is efficient in terms of lookup and avoiding duplicates.
    deciphered_words = set(decipheredtext.split())
    
    # Find what words are in the dictionary, and also in our currently deciphered text.
    common_words = deciphered_words.intersection(dictionary)

    # If the number of words common to both the dictionary and the deciphered 
    # text is high enough (larger than the total number of unique deciphered words / X, where X is a value we can tweak.)
    if len(common_words) > ((len(deciphered_words) // 1.5)):
        return True
    return False

def get_fitness(text):
    """ Function to calculate the fitness value (how closely the deciphered text resembles english)
        of our currently deciphered text, using the various ngramfiles statistics.
    """
    score = 0
    # Calculate the fitness of the text in terms of quadgrams, trigrams and bigrams.
    # Results in slightly longer times but improves the programs ability to find the correct
    # key / higher overall scores after fewer iterations.
    # In my opinion, we could ONLY perform this with quadgrams and come out with near equal
    # results, and lower times.
    qf = quadfitness.get_fitness_score(text)
    tf = trifitness.get_fitness_score(text)
    bf = bifitness.get_fitness_score(text)
    score = qf + tf + bf
    #score += qf
    return score

def cracking(ciphertext):
    """Primary function for cracking substitution cipher. Based on Simulated Annealing techniques."""
    # The essence of this algorithm can be captured in the below pseudo-code / plain english explanation:
    #
    # 1. (First Stage)
    # Generate a random key and assign as 'parent' key
    # Decipher with random parent key
    # Rate fitness of deciphered text and assign as current MAX_SCORE
    # 
    # 2. (Second Stage) Main Loop 
    # WHILE exit_criteria NOT met:
    #      Change key slightly, generating a random neighboring solution and assign as 'child' key
    #      E.g Swap characters
    #      Decipher with this new child key
    #      Meausure new_fitness of deciphered text
    #      IF  new_fitness > MAX_SCORE:
    #          MAX_SCORE = new_fitness
    #          parent key = child key : we now move forward with a new parent key
    #
    # Def: "Neighboring" means there's only one thing that differs between the old solution and the new
    # solution. Effectively, you switch two elements of your solution and re-calculate the cost. The main 
    # requirement is that it be done randomly.


    # Initialize our max_key based off the probability distribution of most common English characters.
    # Our starting max_key is relatively neglible, but the statistical reliability may prove useful on
    # larger pieces of text.
    max_key = list("ETAOINSHRDLUWMFCGYPBKVJXQZ")

    # We make our max_score so low to allow for the logarithmic values.
    max_score = -99e9

    # Assign our inital parent score and key values which are based off the initiliazed maximums / defaults. 
    parent_score,parent_key = max_score,max_key[:]

    # Track the time of our optimal solution. Useful for testing of program, not necessarily as important 
    # in parallel multiprocessing solution as in single thread. Elaborated on in report.
    time_best_solution = 0

    # Start tracking time.
    start_time = time.time()
    
    # We want to keep track of the total number of iterations / random restarts we go through.
    # One of our primary exit criteria.
    # This is essentially a track of how many
    # random restarts we go through in order to try and improve our score and 'climb the hill'. These
    # random restarts are key to avoid becoming stuck in local maxima.
    number_iterations_without_improvement = 0


    i = 0
    # We want to run through the program until the established exit criteria have been met.
    while True:
        
        # Once we have gone through N (in this case 5) random key restarts without
        # improvement to the score / fitness, we want to exit. 
        if number_iterations_without_improvement > 5:
            break

        print("Iteration " + str(i) + " complete.")

        i = i+1

        # Complete random re-shuffle of our current key once it has been unable to
        # make any improvement over the last 1000 iterations of small changes. 
        random.shuffle(parent_key)

        # Create our deciphered text using the newly shuffled parent key.
        deciphered = decipher_text(cipher_text,parent_key)
        
        # Assign our current parent_score (fitness of the deciphered text given the current parent key).
        parent_score = get_fitness(deciphered)

        # We only want the loop to run N (in this case 1000) trials without improvement.
        # This is to avoid going on for too long and getting stuck in a local maxima.
        num_trials = 0
        while num_trials < 1000:
            
            # child is shallow copy of parent key
            child_key = parent_key.copy()

            # assign random indexes for swapping characters in our parent key
            letter1 = random.randint(0,25)
            letter2 = random.randint(0,25)

            # swap two characters in the child_key
            child_key[letter1],child_key[letter2] = child_key[letter2],child_key[letter1]

            # Decipher the cipher text again using our new child key.
            deciphered = decipher_text(cipher_text, child_key)

            # Calculate and assign the fitness score of the text deciphered by current child key.
            child_score = get_fitness(deciphered)

            # If the score obtained by the new child_key is greater
            # than that of the current parents score, update it to the new child_score.
            # Additionally the child_key becomes the new_parent, and we continue forward with it.
            if child_score > parent_score:
                # update parent score
                parent_score = child_score
                # parent_key is updated by current new max child_key
                parent_key = child_key.copy()
                
                # number of trials without improvement can be set back to 0.
                num_trials = 0
            num_trials += 1
        
        # Once the program has failed to imporve it's key / score after 1000 trials,
        # we want to take the best score (the current parent_key / parent_score) from
        # that set of trials and see if it's greater than the max score we have thus far.
        # keep track of best score seen so far
        if parent_score > max_score:
            # if the parent score from taht set of trials is greater, we
            # can reset the number of iterations with max score improvement back to 0.
            number_iterations_without_improvement = 0

            # Update our max_score and max_key to the new max values
            # from the set of trials.
            max_score,max_key = parent_score,parent_key.copy()

            print("New maximum fitness : " + str(max_score))
            print("Discoverd on iteration : " + str(i))
            print("---------------------------------")
            print("Max Key --> " + '-'.join(max_key))
            
            # Find time of current max score. This is most useful in the single threaded solution
            # as it directly correlates as being the time taken for the final solution and output key.
            # This is due to how the exit criteria work when the system is not parallelized.
            time_best_solution = time.time() - start_time

            print("Time taken to find this max score " + str(time_best_solution))
            
            # Decipher the cipher text use our new max (best) key.
            # This print isn't necessarily required, but is useful to see the
            # state of our program, and for testing.
            max_text = decipher_text(cipher_text,max_key)
            print('    plaintext: '+ max_text)

            # Append the max key, and it's relevent fitness score calculated on the text,
            # to the shared syncmanager object. Each of our processes will append it's best result.
            # Which we can then extract to find the optimal key found by the parallel processes.

            final_scores.append((max_key, max_score))
            
            # Another one of our key exit criteria. Calls the function and checks if our max_text
            # thus far meets the exit criteria of having sufficient overlap with the dictionary.
            # Again, this is more useful in the single threaded program, as all our procceses must finish
            # regardless in this solution.
            if check_english_dic(max_text, english_dictionary):
                break
        # If the parent score from the set of trials was not greater than our current max
        # score, we simply return to the beginning to reshuffle the key.
        else:
            number_iterations_without_improvement += 1

    return (max_text, max_key, time_best_solution)


if __name__ == "__main__":
    # Enter file for decrytpion as additional cmd line argument
    # Usage example --> python3 substition_crack.py ciphered-text.txt 
    inputfilename = sys.argv[1]
    
    # Open and read in the cipher text
    with open(inputfilename) as f:
        cipher_text = f.read()
    
    # Change full to upper case, easier to manage as case is (mostly) irrelevant.
    cipher_text = cipher_text.upper()

    processes = []

    for i in range(os.cpu_count()):
        processes.append(Process(target=cracking, args=(cipher_text,)))

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    max_key, max_score = max(final_scores, key=itemgetter(1))
    
    max_text = decipher_text(cipher_text, max_key)

    max_text, max_key, time_best_solution = cracking(inputfilename)
    
    # write deciphered text answer to output file.
    decipheredText = open(inputfilename+"-decrypted.txt", "w")
    decipheredText.write(max_text)
    decipheredText.close()
    
    # write best key found to output file.
    output_key = open(inputfilename+"-key.txt", "w")
    alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    for letter in range(len(alphabet)):
        output_key.write("{} = {}\n".format(alphabet[letter], max_key[letter]))
    output_key.close()


