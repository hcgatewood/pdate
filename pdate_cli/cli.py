#!/usr/bin/env python3

"""
pdate is a basic date conversion tool.
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Iterator

import click
import dateparser
import dateutil.parser
import humanize


class Fmt:
    class E(Enum):
        TS = "timestamp"
        DATE = "date"
        HUMAN = "human"
        HUMAN_PRECISE = "human_precise"

    def __init__(self, ts: bool, date: bool, human: bool, human_precise: bool, *, default: "Fmt.E"):
        self.ts = ts
        self.date = date
        self.human = human
        self.human_precise = human_precise
        if not any((ts, date, human, human_precise)):
            self.ts = default == Fmt.E.TS
            self.date = default == Fmt.E.DATE
            self.human = default == Fmt.E.HUMAN
            self.human_precise = default == Fmt.E.HUMAN_PRECISE

    def __bool__(self):
        return any((self.ts, self.date, self.human, self.human_precise))


@dataclass
class FmtOpts:
    fmt: Fmt
    use_am_pm: bool


@dataclass
class PrintableDate:
    date: datetime
    str: str

    def __bool__(self):
        return bool(self.str)

    def __str__(self):
        return self.str


ParseFn = Callable[[str], datetime]


def make_stripped(parse: ParseFn) -> ParseFn:
    def wrap(arg: str) -> datetime:
        return parse(arg.strip().strip("'").strip('"'))

    return wrap


def parse_dateparser(arg: str) -> datetime:
    dt = dateparser.parse(arg)
    if not dt:
        raise ValueError(f"could not parse date: {arg}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def parse_dateutil(arg: str) -> datetime:
    dt = dateutil.parser.parse(arg)
    if not dt:
        raise ValueError(f"could not parse date: {arg}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def parse_timestamp(arg: str) -> datetime:
    return datetime.fromtimestamp(int(arg)).astimezone()


@dataclass
class Parser:
    name: str
    fn: ParseFn


DefaultParsers: list[Parser] = [
    Parser("dateparser", parse_dateparser),
    Parser("dateparser_stripped", make_stripped(parse_dateparser)),
    Parser("dateutil", parse_dateutil),
    Parser("dateutil_stripped", make_stripped(parse_dateutil)),
    Parser("timestamp", parse_timestamp),
    Parser("timestamp_stripped", make_stripped(parse_timestamp)),
]


@click.command(context_settings=dict(help_option_names=["-h", "--help"], max_content_width=120))
@click.argument("arg", nargs=-1)
@click.option("--now", is_flag=True, help="Print just current date.")
@click.option("--ts", is_flag=True, help="Format output as Unix timestamp.")
@click.option("--date", is_flag=True, help="Format output as human-readable date.")
@click.option("--human", is_flag=True, help="Format output as human-readable date.")
@click.option("--precise", is_flag=True, help="Format output as precise human-readable date.")
@click.option("--verbose", is_flag=True, help="Print debug information.")
@click.option("--sort", is_flag=True, help="Sort output by date. Implies --stdin.")
@click.option("--12", "use_am_pm", is_flag=True, help="Use 12-hour format.")
def cli(arg: list[str], now: bool, ts: bool, date: bool, human: bool, precise: bool, verbose: bool, sort: bool, use_am_pm: bool):
    """
    Parse ARG and format it as a local, human-readable date.

    \b
    If ARG is missing
    - If --now: print current date (default format: Unix timestamp)
    - Else: read from stdin (default format: human-readable date)

    \b
    Supported ARG formats
    - Most date formats, e.g. ISO-8601, RFC-2822, etc.
    - Unix timestamp

    \b
    Timezone considerations
    - For dates without timezone info, UTC is assumed
    - For timestamps, local timezone is assumed
    """
    if arg and now:
        raise click.ClickException("cannot set both ARG and --stdin")
    opts = FmtOpts(Fmt(ts, date, human, precise, default=Fmt.E.DATE), use_am_pm=use_am_pm)

    if arg:
        handle_arg(" ".join(arg), opts, verbose)
        return
    if now:
        opts.fmt = Fmt(ts, date, human, precise, default=Fmt.E.TS)
        handle_no_arg(opts)
        return
    if sort:
        handle_stdin_sorted(sys.stdin.readlines(), opts, verbose)
        return
    handle_stdin(sys.stdin, opts, verbose)


def handle_arg(arg: str, opts: FmtOpts, verbose: bool):
    parsed = get_parsed(arg, opts, verbose)
    if parsed:
        click.echo(parsed)
    else:
        raise click.ClickException("could not parse input")


def handle_stdin(lines: Iterator[str], opts: FmtOpts, verbose: bool):
    for line in (l for line in lines if (l := line.strip())):
        handle_arg(line, opts, verbose)


def handle_stdin_sorted(lines: list[str], opts: FmtOpts, verbose: bool):
    parsed = []
    for line in lines:
        p = get_parsed(line, opts, verbose)
        if not p:
            click.echo(f"Failed to parse: {line}", err=True)
            continue
        parsed.append(p)
    parsed.sort(key=lambda d: d.date)
    for p in parsed:
        click.echo(p)


def handle_no_arg(opts: FmtOpts):
    click.echo(get_current(opts))


def get_parsed(arg: str, opts: FmtOpts, verbose: bool) -> PrintableDate:
    return first(arg, DefaultParsers, opts, verbose)


def get_current(opts: FmtOpts) -> str:
    return fmt_date(datetime.now().astimezone(), opts)


def fmt_date(dt: datetime, opts: FmtOpts) -> str:
    fmt = opts.fmt
    if not fmt:
        raise ValueError("invalid format")

    strs = []
    if fmt.ts:
        strs.append(str(int(dt.timestamp())))
    if fmt.date:
        strs.append(dt.strftime("%A, %B %d, %Y %I:%M:%S %p %Z") if opts.use_am_pm else dt.strftime("%A, %B %d, %Y %H:%M:%S %Z"))
    if fmt.human:
        strs.append(humanize.naturaltime(dt))
    if fmt.human_precise:
        now = datetime.now().astimezone()
        delta = dt - now
        suffix = "ago" if delta.total_seconds() < 0 else "from now"
        human = humanize.precisedelta(delta)
        strs.append(f"{human} {suffix}")

    return "\n".join(strs)


def first(arg: str, parsers: list[Parser], opts: FmtOpts, verbose: bool) -> PrintableDate:
    for parser in parsers:
        try:
            dt = parser.fn(arg)
            return PrintableDate(dt, fmt_date(dt, opts))
        except (ValueError, OverflowError, AttributeError) as e:
            if verbose:
                click.echo(f"Failed to parse as {parser.name}: {e}", err=True)
            continue
    return PrintableDate(datetime.fromtimestamp(0), "")


if __name__ == "__main__":
    cli()
