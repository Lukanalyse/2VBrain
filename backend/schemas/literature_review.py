from pydantic import BaseModel

from schemas.linking import LinkableObject


class LiteratureReviewCreate(BaseModel):
    title: str


class LiteratureReviewDetail(BaseModel):
    review: LinkableObject
    content: str


class LiteratureReviewList(BaseModel):
    reviews: list[LinkableObject]
