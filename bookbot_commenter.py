import datetime, os, pickle, praw, re, requests, time

class redditBot():
    url = 'https://www.googleapis.com/books/v1/volumes?q=intitle:'
    
    def __init__(self) -> None:
        ''' Base class for reddit bots
        '''
        self.rbot = praw.Reddit('bbbot')

        # TODO: fully implement storing seen comment ids so we dont reply to the
        # same comment more than once
        pickle_path = 'seen.pickle'

        if not os.path.exists(pickle_path):
            self.seen = {}
        else:
            with open(pickle_path, 'rb') as f:
                self.seen = pickle.load(f)


class rMonitor(redditBot):
    def _create_book_msg(self, author: str, book_results: dict[str, str], short: bool, title: str) -> str:
        ''' Method iterates over all found books to try to find the first closest
        match (Google API already returns them in closest match to query as well). 

        @param author: author, if any, of book recommended
        @param book_results: book info data dict
        @param short: whether or not the msg needs to be truncated
        @param title: title of book recommended

        @return msg: msg for a given recommendation
        '''
        for book in book_results:
            book = book.get('volumeInfo', {})

            authors = {x.lower() for x in book.get('authors', [''])}
            b_title = book.get('title', '')
            
            # If we have title and no author or title and author match, get book data
            if title.lower() == b_title.lower() and (not author or author.lower() in authors):
                msg = self._get_book_data(book, short)  
                break
        else:
            msg = f'Sorry, I didn\'t quite get that. Found no results for {title}'

            if author:
                msg += f'by {author}'
        
        return msg


    def _get_title_author(self, rec: str) -> tuple[str, str]:
        ''' Method reads recommendation and splits into a book and author name; assumes
        only book name given if no by to split by

        @param rec: recommendation in format \[\[Book name by Author Name\]\] or just  \[\[Book name\]\]

        @return title: cleaned name of book
        @return author: cleaned name of author if any
        '''
        rec = rec[4:-4].split('by')

        author = ''
                
        if len(rec) == 1:
            title = rec[0]
        else:
            title, author = rec
        
        return title.strip(), author.strip()


    def _get_book_data(self, book: dict[str, str], short: bool) -> str:
        ''' Method gets book data and turns it into a comment-style str

        @param book: book info dict
        @param short: Whether or not we need to keep the post short

        @return msg: Book data found
        '''
        # Make sure we dont over run the api limit
        while (datetime.datetime.now() - self.com_start).total_seconds() < 2:
            time.sleep(2)

        title = book.get('title')
        authors = ''.join(book.get('authors', ['']))
        rating = book.get('averageRating')
        link = book.get('infoLink')

        msg = f'[{title}]({link}) by {authors} *received a rating of {rating} on Google Books*.'

        if short is False:
            desc = book.get('description')
            # Attempt to remove useless extra text
            desc = desc.split('Praise for')[0].split('Read all')[0]

            msg += f'\n\n**Description:**\n\n{desc}'
        
        return msg


    def monitor_and_reply(self, sub: str) -> None:
        ''' Method to indefinitely monitor a given subreddit's comment stream, replying
        if beckoned with proper delimiter 
        
        The "delimiter" proposed would be surrounding double brackets, such that
        the bot would look for and parse books by finding [[Book Name by Author Name]]
        with some handling for if someone forgot the author

        @param sub: name of subreddit
        '''
        # NOTE: stream works on comments of comments too
        for comment in sub.stream.comments():
            self.com_start = datetime.datetime.now()

            if rec := re.findall(r'\\\[\\\[.*\\\]\\\]', comment.body):
                body = ''

                while len(body) < 10000 and rec:
                    title, author = self._get_title_author(rec.pop(0))

                    url += title.replace(' ', '+')

                    if author:
                        url += f'+inauthor:{author}'

                    get = requests.get(url)
                
                    body += self._create_book_msg(author=author, title=title, short=len(rec) > 1,
                                                  book_results=get.json().get('items', []))

                comment.reply(body=body)

            self.seen.add(comment.id)

            # TODO: decide when we should dump the current seen to a pickle file,
            # since the stream is indefinite and therefore we won't ever gracefully exit as is


def main():
    SUBREDDIT_NAME = 'pythonforengineers'

    rbot = rMonitor()

    rbot.monitor_and_reply(SUBREDDIT_NAME)
    


if __name__ == '__main__':
    main()