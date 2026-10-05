# Required Tool-Schema Fields as an Exfiltration Channel

A tool provider can require a parameter the user's task does not need, which a
model may fill from its confidential system prompt. In an order-lookup task,
every trial plants five synthetic confidential facts and the schema adds one
required field. On two preregistered models a targeted field returns its fact in
68% of GPT-4o and 59% of Gemini 3 Flash calls, and each other fact in 2% and 1%
of checks. Region, operator, and service-key fields succeed in every call; two of
three fields that only allude to their fact never do. A neutral field returns
none. An exploratory replication on GPT-6.1 Sol, Claude Opus 5.5 and Gemini 3.1
Pro, the last incomplete, shows the same selectivity, by 61.5 to 77.4 percentage
points. In two further preregistered studies with a local handler, a string
pattern that admits the secret does not measurably reduce recovery, and
enumerated, integer, and boolean fields deliver the planted value in 239/240
trials, above guessing rates. A dispatch filter that knows every planted value
blocks plain copies but passes the hexadecimal form in 151/160 and 158/160
trials, and a code split across typed slots in every planted trial. An allowlist
of task arguments, defined by the experimenter, removes them all. When the tool
then refuses the reduced call, the targeted secret moves elsewhere in 0/411
trials, within the stated bound on every leg, one incomplete, and every task
fails. An earlier preregistered hypothesis, that such a field outperforms an
explicit request on most models, failed.
