from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    id: str
    title: str
    selftext: str = Field(default="")
    author: str
    score: int
    num_comments: int
    created_utc: float
    url: str
