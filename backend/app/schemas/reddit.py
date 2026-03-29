from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    id: str
    title: str
    post_body: str = Field(default="")
    subreddit: str
    upvotes: int
    num_comments: int
    created_utc: float
    url: str
