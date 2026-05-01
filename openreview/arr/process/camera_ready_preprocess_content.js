async function process(client, edit, invitation) {
  client.throwErrors = true;

  const texRules = [
    { name: 'TeX environment', regex: /\\begin\{[^}\n]+\}[\s\S]*?\\end\{[^}\n]+\}/ },
    { name: 'TeX command', regex: /\\[A-Za-z]+(?:\*)?\b/ },
    { name: 'TeX escaped symbol', regex: /\\[%&#_$^{}]/ },
    { name: 'TeX display math', regex: /(^|[^\\])\$\$[\s\S]+?\$\$/, trimPrefixCapture: true },
    { name: 'TeX inline math', regex: /(^|[^\\])\$(?:[^$\n]|\\\$)+\$/, trimPrefixCapture: true },
    { name: 'TeX math \\(...\\)', regex: /\\\([\s\S]+?\\\)/ },
    { name: 'TeX math \\[...\\]', regex: /\\\[[\s\S]+?\\\]/ }
  ];

  const markdownRules = [
    { name: 'Markdown link', regex: /\[[^\]\n]+\]\([^)]+\)/ },
    { name: 'Markdown autolink', regex: /<https?:\/\/[^>\s]+>/i },
    { name: 'Markdown fenced code', regex: /```[\s\S]+?```/ },
    { name: 'Markdown code span', regex: /`[^`\n]+`/ },
    { name: 'Markdown emphasis (*)', regex: /(^|[^\w])\*{1,3}[^*\n]+\*{1,3}(?=$|[^\w])/, trimPrefixCapture: true },
    { name: 'Markdown emphasis (_)', regex: /(^|[^\w])_{1,2}[^_\n]+_{1,2}(?=$|[^\w])/, trimPrefixCapture: true }
  ];

  const normalize = (value) => typeof value === 'string'
    ? value.replace(/\r\n?/g, '\n').trim()
    : '';

  const findViolation = (text, rules) => {
    for (const rule of rules) {
      const match = text.match(rule.regex);
      if (match) {
        const snippet = rule.trimPrefixCapture
          ? match[0].slice((match[1] || '').length)
          : match[0];
        return {
          rule: rule.name,
          snippet: snippet.replace(/\s+/g, ' ').trim().slice(0, 80)
        };
      }
    }
    return null;
  };

  for (const field of ['title', 'abstract']) {
    const value = normalize(edit.note?.content?.[field]?.value);
    if (!value) {
      continue;
    }

    const texViolation = findViolation(value, texRules);
    if (texViolation) {
      return Promise.reject(new OpenReviewError({
        name: 'Error',
        message: `${field} cannot contain TeX markup (${texViolation.rule}). Detected: ${texViolation.snippet}`
      }));
    }

    const markdownViolation = findViolation(value, markdownRules);
    if (markdownViolation) {
      return Promise.reject(new OpenReviewError({
        name: 'Error',
        message: `${field} cannot contain Markdown markup (${markdownViolation.rule}). Detected: ${markdownViolation.snippet}`
      }));
    }
  }

  return Promise.resolve();
}
