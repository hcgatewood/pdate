# PDate

PDate make dates and times human-readable.

## Install

```bash
pip install pdate_cli
```

## Features

### Quick check

```bash
$ pdate --now
1753307983

$ pdate --now --date
Wednesday, July 23, 2025 05:04:09 PM CDT
```

### Convert: flexible input formats

```bash
# Most formats accepted, e.g. ISO-8601, RFC-2822, etc.

$ pdate 2024-11-25T20:10:46Z
Monday, November 25, 2024 02:10:46 PM CST

$ pdate 12 hours ago
Wednesday, July 23, 2025 12:07:13 AM CDT
```

### Convert: choice of output format

```bash
$ pdate 2024-11-25T20:10:46Z --human
7 months ago

$ pdate 2024-11-25T20:10:46Z --precise
7 months, 26 days, 1 hour, 58 minutes and 24.89 seconds ago

$ pdate 2024-11-25T20:10:46Z --date --precise
Monday, November 25, 2024 02:10:46 PM CST
7 months, 26 days, 1 hour, 58 minutes and 46.01 seconds ago
```

### Batch: read from stdin, sort, etc.

```bash
$ echo 100000000 | pdate
Saturday, March 03, 1973 03:46:40 AM CST

$ echo -e '2024-11-25T20:10:46Z\n2024-11-25T20:10:46Z\n100000000' | pdate --sort
Saturday, March 03, 1973 03:46:40 AM CST
Monday, November 25, 2024 02:10:46 PM CST
Monday, November 25, 2024 02:10:46 PM CST
```

## Help pages

```text
$ pdate --help
Usage: pdate [OPTIONS] [ARG]...

  Parse ARG and format it as a local, human-readable date.

  If ARG is missing
  - If --now: print current date (default format: Unix timestamp)
  - Else: read from stdin (default format: human-readable date)

  Supported ARG formats
  - Most date formats, e.g. ISO-8601, RFC-2822, etc.
  - Unix timestamp

  Timezone considerations
  - For dates without timezone info, UTC is assumed
  - For timestamps, local timezone is assumed

Options:
  --now       Print just current date.
  --ts        Format output as Unix timestamp.
  --date      Format output as human-readable date.
  --human     Format output as human-readable date.
  --precise   Format output as precise human-readable date.
  --verbose   Print debug information.
  --sort      Sort output by date. Implies --stdin.
  --12        Use 12-hour format.
  -h, --help  Show this message and exit.
```
