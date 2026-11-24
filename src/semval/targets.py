"""What a tagger sees: a set of target values with definitions and examples.

A ``TargetSet`` is built from one named level of a framework file
(``Framework.target_set``). Taggers never read the framework itself, so swapping the
level or the framework changes the targets without touching tagger code.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from semval.checks import full_sentence, no_duplicates, slug_id


class OfficialDefinition(BaseModel):
    """A source's own definition of a target, with where it was taken from.

    ``text`` is ``None`` when the licence keeps the verbatim text out of the public repo:
    then ``local_only`` is true and the text is merged in from a git-ignored local file.
    """

    model_config = ConfigDict(extra="forbid")

    citation: str = Field(min_length=1)
    page: str = Field(min_length=1)
    text: str | None = None
    local_only: bool = False

    @model_validator(mode="after")
    def _text_or_local(self) -> "OfficialDefinition":
        if self.text is not None and not self.text.strip():
            raise ValueError("official text must not be blank")
        if self.text is None and not self.local_only:
            raise ValueError("official text is required unless local_only is true")
        return self


class TargetDef(BaseModel):
    """One value a tagger can assign. ``definition`` is our plain-English wording."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    definition: str
    official: OfficialDefinition | None = None
    examples_endorse: list[str] = Field(default_factory=list)
    examples_reject: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id(cls, v: str) -> str:
        return slug_id(v)

    @field_validator("definition")
    @classmethod
    def _definition(cls, v: str) -> str:
        return full_sentence(v)


class TargetSet(BaseModel):
    """The targets of one framework level, in the order the framework file gives them."""

    model_config = ConfigDict(extra="forbid")

    framework_id: str
    level_id: str
    targets: list[TargetDef] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> "TargetSet":
        no_duplicates(self.ids(), "target id")
        return self

    def ids(self) -> list[str]:
        return [t.id for t in self.targets]
