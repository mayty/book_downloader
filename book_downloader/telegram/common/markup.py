from html import escape
from string.templatelib import Interpolation, Template


class HtmlTag:
    tag: str

    def __init__(self, value: str | Template | HtmlTag) -> None:
        self.value = value if value is not None else '<null>'

    @staticmethod
    def escape_if_needed(value: object) -> str:
        if isinstance(value, HtmlTag):
            return str(value)
        return escape(str(value))

    def assemble(self, escaped_text: str) -> str:
        return f'<{self.tag}>{escaped_text}</{self.tag}>'

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return self.assemble(escape(self.value))

        if isinstance(self.value, HtmlTag):
            return self.assemble(str(self.value))

        assert isinstance(self.value, Template)

        result = ''
        for element in self.value:
            if isinstance(element, Interpolation):  # type: ignore[misc]
                if element.conversion is not None:
                    msg = 'Conversion is not supported'
                    raise ValueError(msg)
                if element.format_spec:
                    msg = 'Format spec is not supported'
                    raise ValueError(msg)
                value = element.value  # type: ignore[misc]
            else:
                value = element
            result += self.escape_if_needed(value)  # type: ignore[misc]

        return self.assemble(result)


class BoldTag(HtmlTag):
    tag = 'b'


class HyperlinkTag(HtmlTag):
    tag = 'a'

    def __init__(self, value: str | Template | HtmlTag, href: str) -> None:
        super().__init__(value)
        self.href = href

    def assemble(self, escaped_text: str) -> str:
        return f'<{self.tag} href="{escape(self.href)}">{escaped_text}</{self.tag}>'


class ItalicTag(HtmlTag):
    tag = 'i'


class QuoteTag(HtmlTag):
    tag = 'blockquote'


class RawTag(HtmlTag):
    def __init__(self, value: str) -> None:
        super().__init__(value)

    def __str__(self) -> str:
        assert isinstance(self.value, str)
        return self.value
