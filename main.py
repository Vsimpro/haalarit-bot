import time, requests

from selenium import webdriver
from bs4      import BeautifulSoup


class Bot:
    def __init__(self, site="", browser=True, name="b0t"):
        self.site = site
        self.name = name
        self.storage = { }

        self.limit = 0
        self.count = 0
        self.offset = 3

        self.soup = None
        
        # init browser
        if browser:
            self.driver = webdriver.Firefox()
            self.driver.get(site)  
        
#
#   === GAME FUNCTIONALITIES ===
#

    # Play the quiz. 
    def play(self):
        # Make sure set of correct answers is present.
        if self.storage == { }:
            self.parse_answers()

        self.count = 0
        self.limit = len(self.storage) - self.offset
        for _ in range(len(self.storage)):
            try:
                time.sleep(5 / 10)
                
                # See if scoreboard appears. If it does, end the loop.
                self.soup = BeautifulSoup(self.driver.page_source, "html.parser")                
                if self.soup.find(string="Tallenna tulos") != None:
                    break

                # If the question limit is met, end the game.
                selection_status = False
                if self.count >= self.limit:
                    print("\t* Limit reached *")
                    self.end_game()
                    break    
                
                # If "choose" returns False, somethings wrong.
                if selection_status == self.choose(True):
                    break              

            except Exception as e:
                print(e)

        print("\n -- Game Done. --")
        return True

    # Insert the player name into the scoreboard.
    def insert_name(self):
        time.sleep(1)
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        time.sleep(5 / 10)
        self.driver.find_element(by="xpath", value="//input[@title='nimi']").send_keys(self.name)
        time.sleep(5 / 10)
        self.driver.find_element(by="xpath", value="//button").click()
        time.sleep(10)
        #self.driver.close()

    # Choose the desired answer. Correct = False for the wrong answer, and True for the correct.
    def choose(self, correct=True):
        try: 
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
            image = self.soup.find_all("img", class_="Question_question-img__22zm6")[0].get("src")
            if not image in self.storage:
                print(" ! Could not find image from storage. ")
                return False
            
            # Go through all of the options and pick the desired one:
            for option in self.soup.find_all("div", class_="Alternative_alternative__2orVq"):                   
                if (option.text == self.storage[image]) == correct:
                    print(" + Found the correct answer.. " * correct, " - Found the wrong answer.. " * (correct == False) ,end=" ")
                    print(self.count)

                    self.click_div(option.text)
                    return True

            # If no answer match; somethings wrong. 
            print("! DIDN'T FIND DESIRED ANSWER.")
            for option in self.soup.find_all("div", class_="Alternative_alternative__2orVq"):
                print(f"{option.text} | {self.storage[image]} ")
            
            return False
        
        # If you go over the limit, the website breaks, as no new questions appear.
        except IndexError:
            print(" !! Website broken. ")
            return False
                
    # As the game needs 3 wrong answers to "end" it, choose 3 wrong intentionally to exit.
    def end_game(self):
        for _ in range(0, 3):
            time.sleep(5 / 10)
            self.choose(False)

    # Return "king of the hill" status as false / true. 
    # If someone else is on the board, we're not the king.
    def check_leaderboard(self):
        self.end_game()
        time.sleep(5 / 10)
        
        king = True
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        print(" -- Checking leaderboard --")
        for row in self.soup.find_all("tr"):
            player = str(row.find_all("td")[2]).replace("<td>", "").replace("</td>", "")
            
            # If we occupy the leaderboard, continue.
            if player == "Nimi" or player == self.name: 
                continue
            
            print(" !! Someone else occupies the board: ", player)
            king = False

        print(" -- Done! --")
        return king

#
#   === SUPPORTING FUNCTIONS ===
#

    # Find the div with the correct option, and then click it.
    def click_div(self, correct_option):
        try:
            self.driver.find_element(by="xpath", value=f"//div[contains(text(), '{correct_option}')]").click()
            self.count += 1
        except Exception as e:
            print(e)
            return False
        
        return True

    # get all the correct answers from the static JS file.
    def parse_answers(self):
        static_js = "main.45acba1b.chunk.js"

        # get the static JS used to play the game.
        request = requests.get(self.site + "/static/js/" + static_js)
    
        # Find all the questions.
        for question in request.text.split("questions:[{")[1].split("}]"):
            try:
                first_id = False
                # Find all the correct answers.
                for line in question.split(","):
                    if "results:[{:" in line: 
                        break

                    if "id" in line and not first_id:
                        first_id = True
                        continue

                    if "img" in line:
                        link = line.split("img:\"")[1].split("\"")[0]
                        self.storage[link] = ""
                        continue

                    if "text:" in line:
                        text = line.split("text:\"")[1].split("\"")[0]
                        continue

                    if "isCorrect:" in line and "!0" in line:
                        # Correct UTF-8 errors.
                        self.storage[link] = \
                            text.replace("\\xe4", "ä").replace("\\xf6", "ö")\
                                .replace("\\xc3\\xa4", "Ã¤")
                        
                        link = ""
                        break

            except IndexError:
                break

def main():
    bot = Bot("https://haalar.it")
    bot.parse_answers()

    while 1:
        while 1:
            # Check leaderboard every 20s.
            
            king_status = bot.check_leaderboard()
            if not king_status:
                # If we don't dominate the board, play the game again.
                break

            time.sleep(20)

        # Leaderboard consists of 9 places, fill them: 
        for _ in range(0, 9):
            bot.driver.get(bot.site)
            bot.play()
            bot.insert_name()

        

if __name__ == "__main__": 
    try:
        main()
    
    except KeyboardInterrupt:
        print(" ** EXITING GAME **")
        exit()
