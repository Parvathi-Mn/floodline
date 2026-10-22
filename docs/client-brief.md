# Client brief: Kerala SDMA Flood Helpline Agent

> Status: **Draft v0.2**. Targets and numbers are initial and will be revised after the first eval runs (see `evals/`).
> This is a portfolio project. It is not an official KSDMA product.

## 1. Purpose

Kerala faces repeated floods and landslides (2018, 2019, 2024). During heavy rain, the disaster control rooms get far more calls than they can answer, and many callers ask the same few questions.

Floodline is a multilingual voice and chat agent that handles those repeated questions instantly, in the caller's own language, using live data. It hands over to a human whenever a life may be at risk or the agent cannot help.

**The agent's job:** tell the caller how risky their area is right now, where the nearest safe relief camp is, and what to do next. It does not replace emergency services.

## 2. Client and stakeholders

|                        Who                         |                        Interest                                |
|----------------------------------------------------|----------------------------------------------------------------|
| Kerala State Disaster Management Authority (KSDMA) | Fewer repeat calls, consistent official messaging              |
| District control rooms                             | Receive only the cases that need a human, with a ready summary |
| Callers                                            | A fast, correct answer in their language                       |

## 3. Who calls, and when

| Caller                                                    | Typical situation                                    | What they need                                   |
|-----------------------------------------------------------|------------------------------------------------------|--------------------------------------------------|
| Family in a low-lying area (e.g. Kuttanad, Alappuzha)     | Water rising near the house                          | Is my area at risk? Where do we go?              |
| Resident in a landslide-prone area (e.g. Wayanad, Idukki) | Days of heavy rain, slope looks unstable             | Risk level, whether to evacuate, nearest camp    |
| Tourist (e.g. Munnar)                                     | Road closed, unfamiliar area, may not know Malayalam | Safety status, what to do, where to stay         |
| Migrant worker (e.g. Ernakulam)                           | Cannot read Malayalam warnings                       | Plain-language help (Hindi planned for later)    |
| Relative abroad or in another state                       | Worried about family back home                       | district at risk, how to reach the control room? |
| Fisherfolk and farmers                                    | Deciding whether to go out or move equipment         | Current warning level and rainfall outlook       |

## 4. Channels and languages

**Channels (in build order):** web chat, then browser voice, then a WhatsApp-style chat view. Real phone telephony is an optional extension.

**Languages:** Malayalam, English, Manglish (Malayalam typed in English letters, e.g. "vellam keri, enthu cheyyum?"). Hindi is a possible later addition.

**Language detection:**
1. Detect the language from the caller's first message and reply in it.
2. If the first message is unclear (very short, mixed, or a name only), ask once: "Malayalam, English, or Manglish?"
3. If the caller switches language mid-conversation, follow them.
4. Voice calls: if speech recognition confidence is low twice in a row, offer to switch to chat or hand over to a human.

## 5. What the agent does (call flow)

1. **Greet and set expectations:** say it is an automated assistant and give the emergency number (112) up front.
2. **Safety check first:** ask, or listen for, whether anyone is in immediate danger. If yes, go to escalation (section 7) immediately.
3. **Collect minimum details:** caller's first name (optional) and location (district, then place or landmark).
4. **Look up facts using tools** (never from the model's memory): current risk level for the district, active alerts, nearest relief camp with address and capacity, and relevant helpline numbers.
5. **Give a clear next step:** a short answer, then one action. Keep spoken answers under about 30 seconds.
6. **Confirm and close:** ask whether the caller needs anything else, repeat the key instruction, offer to hand over to a human.

## 6. What the agent must never do

1. **Never invent facts.** Risk levels, camp locations, capacities and phone numbers come only from tools or the client config. If the data is missing, say so and give the nearest verified number.
2. **Never leave the caller without a next step.** Every conversation ends with an action: a safe location, a number to call, or a human handover. (Never leave without a *next step*, which is not the same as always having an answer.)
3. **Never give directions through areas reported as flooded or blocked.** If the route status is unknown, say so.
4. **Never predict a specific event** such as "the dam will break" or "your house will flood". Only report official alert levels and the current risk score.
5. **Never promise rescue or arrival times.** Only the control room can dispatch help.
6. **Never give medical advice** beyond "call 112 or 108".
7. **Never ask for sensitive data** (Aadhaar, bank or OTP details, passwords).
8. **Never argue, lecture, or blame** the caller. Stay calm and short, especially with a panicked caller.

## 7. Escalation to a human

**Immediate emergency (do not continue the normal flow):**
- Someone is trapped, in rising water, injured, or unconscious
- A landslide or building collapse has happened
- Words or phrases such as "help", "drowning", "trapped", or their Malayalam and Manglish equivalents
- Children, elderly or disabled people are in danger

Action: tell the caller to call **112** now, give the district control room number, and flag the conversation as `EMERGENCY` in the logs for human follow-up.

**Normal handover (non-emergency):**
- The caller asks for a human
- The agent has not understood the caller after two attempts
- A needed tool fails or returns no data
- The caller is distressed or abusive and the agent cannot calm the situation

**Handover packet:** caller name (if given), language, district and location, summary of the conversation, and the reason for handover.

## 8. Data and privacy

- Collect only what is needed: first name (optional) and location. No ID numbers.
- Tell the caller at the start that conversations are logged to improve the service.
- Logs are stored locally in SQLite. **Only synthetic test conversations are used in this repo. No real caller data.**
- The LLM provider's terms may allow it to use free-tier prompts for model improvement. This is another reason to test only with synthetic data.

## 9. Degraded mode (when things fail)

| Failure                          | Agent behaviour                                                                          |
|----------------------------------|------------------------------------------------------------------------------------------|
| Weather or risk data unavailable | Say live data is not available right now. Give the district control room number and 112. |
| LLM provider error or rate limit | Fall back to a fixed safe message with emergency numbers.                                |
| Speech recognition fails (voice) | Offer text chat or a human.                                                              |
| Location not recognised          | Ask for the district name, and offer a list of the 14 districts.                         |

## 10. Success metrics

Targets are initial and will be revised once we have eval data.

| Metric                      | Definition                                                                                              | Initial target             |
|-----------------------------|---------------------------------------------------------------------------------------------------------|----------------------------|
| Resolution rate             | Share of conversations ending with a given next step (camp, number, or handover) without a human needed | 70% or higher              |
| Safety escalation recall    | Emergency scenarios correctly escalated to 112 and a human                                              | 100% on the eval set       |
| Factual accuracy            | Facts in answers that match tool output (risk level, camp, numbers)                                     | 100%, no invented facts    |
| Time to first useful answer | From first message to a risk level or safe location                                                     | Under 30 seconds           |
| Language match              | Reply language matches caller language                                                                  | 95% or higher              |
| Escalation rate             | Share of conversations handed to a human (watch for too high and too low)                               | Track, no fixed target yet |
| Drop-off rate               | Callers who leave before getting a next step                                                            | Under 15%                  |
| Caller satisfaction         | Optional "Was this helpful?" at the end                                                                 | Track                      |

## 11. Out of scope for v1

- Dispatching rescue teams or tracking ambulances
- Predicting floods days ahead (we report current conditions and official alerts)
- Real phone-number integration (telephony), planned as an extension
- Languages other than Malayalam, English and Manglish (Hindi may come later)

## 12. Assumptions and open questions

- Emergency numbers need verification on official KSDMA and government pages before use. Working list (all **unverified** until checked): 112 (national emergency), district control rooms (1077), ambulance (108), police (100), fire (101).
- Relief camp data: where will it come from? For v1 we use sample data and label it clearly as sample data.
- Does the client want a human callback if the agent hands over, or a live transfer?
- Who owns the final wording of safety messages? In a real deployment, KSDMA would approve them.