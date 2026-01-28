# Legal Information

This document contains important legal information about TokenCrush, including disclaimers, third-party API terms, and dependency licenses.

---

## ⚠️ Important Notices

### Age Requirement
**You must be 18 years or older to use this software.** Some third-party APIs (notably Google Gemini) require users to be at least 18 years old.

### Regional Restrictions (EU/EEA/UK/Switzerland)
**⚠️ CRITICAL: If you are located in the European Union, European Economic Area, United Kingdom, or Switzerland:**

- **Google Gemini Free Tier CANNOT be used** in your region
- You **MUST use the paid tier** of Google Gemini API if you want to use Gemini models
- See: https://ai.google.dev/gemini-api/terms

---

## Disclaimer of Warranty

TokenCrush is licensed under the MIT License. As stated in the LICENSE file:

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

This means:
- No guarantees about functionality, accuracy, or reliability
- Use at your own risk
- Authors are not liable for any damages or issues arising from use

---

## Third-Party API Terms of Service

TokenCrush integrates with several third-party APIs. **You are responsible for complying with their terms of service.**

### Google Gemini API

**Terms:** https://ai.google.dev/gemini-api/terms

**Key Requirements:**
- ✅ **Age 18+ required** - You must be at least 18 years old
- ⚠️ **EU/EEA/UK/Switzerland**: Free tier CANNOT be used. Paid tier required.
- ❌ Cannot use for services directed at children or minors
- ❌ Cannot develop competing AI models using Gemini outputs
- ❌ Cannot reverse engineer the Gemini models
- 📊 Rate limits apply (varies by tier)
- 🔑 You must obtain your own API key from Google AI Studio

**Important:** Google reserves the right to modify or terminate the service at any time.

### Groq API

**Terms:** https://groq.com/terms-of-use

**Key Requirements:**
- 📊 Rate limits apply (varies by tier)
- 🔑 You must obtain your own API key from Groq
- ❌ Cannot use for illegal purposes
- ❌ Cannot attempt to reverse engineer Groq's infrastructure
- 📝 Usage data may be collected for service improvement

**Important:** Groq provides high-speed inference but availability may vary.

### DeepSeek API

**Terms:** https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html

**Key Requirements:**
- 🏢 Operated by DeepSeek (Hangzhou DeepSeek Artificial Intelligence Co., Ltd.) - Chinese company
- 🔑 You must obtain your own API key from DeepSeek
- ⚠️ Service may change, be suspended, or terminated at any time without notice
- 📊 Rate limits apply
- 🌍 Subject to Chinese laws and regulations
- 📝 Usage data may be processed in accordance with DeepSeek's privacy policy

**Important:** As a Chinese company, DeepSeek is subject to Chinese data protection and AI regulations.

### Ollama (Local Models)

**Website:** https://ollama.com

**Key Information:**
- ✅ Runs locally on your machine - no API key required
- 📦 Model licenses vary by model:
  - **Llama models**: Meta Llama Community License
  - **DeepSeek models**: DeepSeek License
  - **Mistral models**: Apache 2.0
  - **Gemma models**: Gemma Terms of Use
- ⚠️ You are responsible for complying with individual model licenses
- 💻 Requires sufficient local compute resources (CPU/GPU, RAM)

**Important:** Check each model's license before use, especially for commercial purposes.

---

## Dependency Licenses

TokenCrush uses the following open-source dependencies:

| Dependency | License | Commercial Use | Notes |
|------------|---------|----------------|-------|
| **LLMLingua** | MIT (Microsoft) | ✅ Allowed | Prompt compression library |
| **LiteLLM** | MIT | ✅ Allowed | Unified LLM API interface |
| **FAISS** | MIT (Meta) | ✅ Allowed | Vector similarity search |
| **sentence-transformers** | Apache 2.0 | ✅ Allowed | Embedding models |
| **Typer** | MIT | ✅ Allowed | CLI framework |
| **Rich** | MIT | ✅ Allowed | Terminal formatting |
| **httpx** | BSD-3-Clause | ✅ Allowed | HTTP client |
| **Pydantic** | MIT | ✅ Allowed | Data validation |
| **PyYAML** | MIT | ✅ Allowed | YAML parsing |

All dependencies permit commercial use under their respective licenses.

---

## Data Privacy & Security

### API Keys
- 🔐 **Never share your API keys** with anyone
- ❌ **Never commit API keys** to version control (git)
- 💾 Store API keys securely (use environment variables or secure key management)
- 🔄 Rotate keys regularly if exposed

### Data Handling
- 💾 **Local cache**: TokenCrush caches compressed prompts locally in `~/.tokencrush/cache/`
- 🌐 **API data**: When you use third-party APIs, your prompts are sent to those services
- 📝 **Logging**: TokenCrush logs operations locally; logs may contain prompt metadata
- ⚠️ **Sensitive data**: Do not include sensitive, confidential, or personal information in prompts

### Third-Party Data Policies
Each API provider has their own data retention and privacy policies:
- **Google Gemini**: See https://ai.google.dev/gemini-api/terms
- **Groq**: See https://groq.com/privacy-policy
- **DeepSeek**: See https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html
- **Ollama**: Data stays local (no external transmission)

---

## Rate Limits & Service Availability

### API Rate Limits
All third-party APIs impose rate limits:
- **Free tiers**: Typically 15-60 requests per minute
- **Paid tiers**: Higher limits, varies by plan
- **Exceeding limits**: May result in temporary blocks or errors

TokenCrush does not guarantee availability of third-party services.

### Service Interruptions
Third-party APIs may experience:
- Downtime or maintenance windows
- Rate limit changes
- Terms of service changes
- Service discontinuation

**You are responsible for monitoring API status and adapting to changes.**

---

## Limitation of Liability

**IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

This includes but is not limited to:
- ❌ Data loss or corruption
- ❌ Service interruptions or downtime
- ❌ API costs incurred from usage
- ❌ Inaccurate or harmful outputs from LLMs
- ❌ Violations of third-party terms of service
- ❌ Security breaches or exposed API keys
- ❌ Any other direct, indirect, incidental, or consequential damages

---

## No Legal Advice

**This document does not constitute legal advice.** It is provided for informational purposes only.

- 📚 You should review all third-party terms of service yourself
- ⚖️ Consult a lawyer if you have legal questions about usage
- 🌍 Comply with all applicable laws in your jurisdiction
- 🏢 If using for commercial purposes, ensure compliance with all licenses

---

## Compliance Checklist

Before using TokenCrush, ensure you:

- [ ] Are at least 18 years old
- [ ] Have read and agree to the MIT License terms
- [ ] Have read and agree to all applicable third-party API terms
- [ ] Understand regional restrictions (EU/EEA/UK/Switzerland for Gemini)
- [ ] Have obtained necessary API keys from providers
- [ ] Will not share or commit API keys to version control
- [ ] Will not use for services directed at minors
- [ ] Will not include sensitive/confidential data in prompts
- [ ] Understand that no warranties are provided
- [ ] Accept all risks and limitations of liability

---

## Updates to This Document

This legal information may be updated as:
- Third-party terms of service change
- New dependencies are added
- New API integrations are added
- Legal requirements evolve

**Check this file regularly for updates.** Continued use of TokenCrush after updates constitutes acceptance of the new terms.

---

## Contact & Reporting Issues

- 🐛 **Bug reports**: Open an issue on GitHub
- 🔒 **Security issues**: Report privately to maintainers
- ❓ **Questions**: Check documentation first, then open a discussion

**Do not include API keys, credentials, or sensitive data in bug reports.**

---

**Last Updated:** January 28, 2026

**Version:** 1.0.0
