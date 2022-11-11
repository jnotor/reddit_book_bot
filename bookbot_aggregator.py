import praw, re, sys
from collections import deque


class rAggregator():
    url = 'https://www.googleapis.com/books/v1/volumes?q=intitle:'
    
    def __init__(self) -> None:
        ''' Base class for reddit bots
        '''
        self.rclient = praw.Reddit('personal')


    def _parse_comment(self, comment: str) -> str:
        msg = ''

        # TODO: write regex pattern matching to try to discern when ppl are giving recs
        
        return msg


    def get_reqs(self, target: str) -> str:
        ''' Method parses all comments of a given post for recommendations into
        a str output for me to then use/post LOL

        @param target: link to post

        @return msg: msg to reply with
        '''
        msg = ''

        # parse the web url for id
        webid = target.split('/comments/')[-1].split('/')[0]

        submission = self.rclient.submission(webid)

        queue = deque(submission.comments)

        while queue:
            current = queue.popleft()

            # NOTE: need to handle the more comments case better but be careful with api requests
            if not isinstance(current, praw.models.MoreComments):
                self._parse_comment(current.text)
                
                queue.extend(current.replies)

        return msg


def main():
    link = sys.argv[1]
    
    rbot = rAggregator()

    with open('msg.txt', 'r') as f:
        f.write(rbot.get_reqs(link))


if __name__ == '__main__':
    main()