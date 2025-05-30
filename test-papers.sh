#!/bin/bash

# Store a test AI security paper with full AI analysis
curl -X POST "http://localhost:8080/newsletter/store-paper" \
  -H "Content-Type: application/json" \
  -u "admin:changeme" \
  -d '{
    "arxiv-id": "2024.12345v3",
    "title": "Advanced Jailbreaking Techniques for Large Language Models: A Comprehensive Analysis of Prompt Injection Vulnerabilities",
    "abstract": "Large Language Models (LLMs) have demonstrated remarkable capabilities across various domains, but they remain vulnerable to adversarial attacks through sophisticated prompt injection techniques. This paper presents a comprehensive analysis of advanced jailbreaking methods that can bypass current safety measures implemented in state-of-the-art language models. We introduce three novel attack vectors: (1) Multi-step semantic manipulation through context window exploitation, (2) Cross-lingual prompt injection using low-resource languages, and (3) Embedding-space adversarial examples that operate below the token level. Our evaluation across five major LLM architectures (GPT-4, Claude, PaLM-2, LLaMA-2, and Gemini) reveals critical vulnerabilities in their safety alignment mechanisms. We demonstrate that our techniques achieve a 87.3% success rate in eliciting harmful outputs while maintaining semantic coherence. Furthermore, we propose a novel defense framework called Adaptive Safety Filtering (ASF) that reduces successful attacks by 94.2% with minimal impact on model performance. Our findings highlight the urgent need for more robust safety measures in LLM deployment and provide actionable recommendations for developing resilient AI systems.",
    "authors": "Sarah Chen, Michael Rodriguez, Dr. Amit Patel, Prof. Lisa Zhang",
    "published": "2024-05-15T10:30:00Z",
    "link": "http://arxiv.org/abs/2024.12345",
    "pdf-link": "http://arxiv.org/pdf/2024.12345.pdf",
    "relevant_for": ["red_teaming", "safety"],
    "topics": ["red_teaming"],
    "search_category": "red_teaming",
    "key_points": [
      "Introduces three novel jailbreaking attack vectors including multi-step semantic manipulation and cross-lingual prompt injection",
      "Demonstrates 87.3% success rate across five major LLM architectures (GPT-4, Claude, PaLM-2, LLaMA-2, Gemini)",
      "Reveals critical vulnerabilities in current safety alignment mechanisms of state-of-the-art language models",
      "Proposes Adaptive Safety Filtering (ASF) defense framework that reduces successful attacks by 94.2%",
      "Provides comprehensive evaluation methodology for testing LLM robustness against adversarial prompt attacks"
    ],
    "conclusion": "This research exposes significant vulnerabilities in current LLM safety mechanisms and provides both offensive techniques and defensive solutions. The high success rates achieved across multiple model architectures indicate that existing safety measures are insufficient against sophisticated adversarial attacks. The proposed ASF framework offers a promising direction for improving model robustness while maintaining performance.",
    "relevance_explanation": "This paper is highly relevant for AI security researchers as it provides practical techniques for testing LLM robustness, reveals systematic vulnerabilities across major models, and offers concrete defensive strategies. The research methodology and attack vectors can be used to evaluate and improve the security posture of AI systems in production environments."
  }'

echo -e "\n\n=== Testing with Safety paper ==="

# Store another test paper for Safety topic with AI analysis
curl -X POST "http://localhost:8080/newsletter/store-paper" \
  -H "Content-Type: application/json" \
  -u "admin:changeme" \
  -d '{
    "arxiv-id": "2024.67890v3", 
    "title": "Constitutional AI: Harmlessness from AI Feedback at Scale",
    "abstract": "Training AI systems to be helpful, harmless, and honest presents significant challenges as models become more capable. This work introduces Constitutional AI (CAI), a method for training AI assistants to follow a set of principles or constitution without human supervision of harmful outputs. Our approach begins with supervised learning from human feedback to train a helpful RLHF model. We then use the model to generate responses to harmful prompts, which are then critiqued and revised according to a set of constitutional principles. This creates a dataset of harmless behavior without requiring humans to write responses to harmful questions. We train a Preference Model (PM) on this revised data and use it for Reinforcement Learning from AI Feedback (RLAIF). We find that Constitutional AI improves on the initial RLHF model across three measures: helpfulness, harmlessness, and honesty. Our constitutional approach reduces harmful outputs by 85% while maintaining or improving helpfulness scores. The method scales efficiently, reducing the need for human oversight in safety training by 73%. We demonstrate the effectiveness of our approach across models ranging from 13B to 175B parameters.",
    "authors": "Yuntao Bai, Andy Jones, Kamal Ndousse, Amanda Askell, Anna Chen, Nova DasSarma, Dawn Drain, Stanislav Fort, Deep Ganguli, Tom Henighan, Nicholas Joseph, Saurav Kadavath, Jackson Kernion, Tom Conerly, Sheer El-Showk, Nelson Elhage, Zac Hatfield-Dodds, Danny Hernandez, Tristan Hume, Scott Johnston, Shauna Kravec, Liane Lovitt, Neel Nanda, Catherine Olsson, Dario Amodei, Tom Brown, Jack Clark, Sam McCandlish, Chris Olah, Ben Mann, Jared Kaplan",
    "published": "2024-05-12T14:22:00Z",
    "link": "http://arxiv.org/abs/2024.67890",
    "pdf-link": "http://arxiv.org/pdf/2024.67890.pdf",
    "relevant_for": ["safety"],
    "topics": ["safety"],
    "search_category": "safety",
    "key_points": [
      "Introduces Constitutional AI (CAI) method for training AI systems to follow ethical principles without human supervision",
      "Uses Reinforcement Learning from AI Feedback (RLAIF) instead of requiring human reviewers for harmful content",
      "Reduces harmful outputs by 85% while maintaining helpfulness across models from 13B to 175B parameters",
      "Decreases need for human oversight in safety training by 73%, making safety training more scalable",
      "Demonstrates effectiveness across three key measures: helpfulness, harmlessness, and honesty"
    ],
    "conclusion": "Constitutional AI represents a breakthrough in scalable AI safety training by enabling models to self-correct harmful behaviors according to predefined principles. This approach significantly reduces the human labor required for safety training while achieving better safety outcomes, making it a practical solution for deploying safer AI systems at scale.",
    "relevance_explanation": "This research is crucial for AI safety practitioners as it provides a scalable method for training safer AI systems without extensive human oversight. The technique addresses one of the key bottlenecks in AI safety - the need for human reviewers to label harmful content - and demonstrates significant improvements in model safety across multiple scales and metrics."
  }'

echo -e "\n\n=== Testing with Governance paper ==="

# Store a test paper for Governance topic with minimal analysis
curl -X POST "http://localhost:8080/newsletter/store-paper" \
  -H "Content-Type: application/json" \
  -u "admin:changeme" \
  -d '{
    "arxiv-id": "2024.11111v3",
    "title": "AI Governance Frameworks: A Comparative Analysis of Regulatory Approaches Across Global Jurisdictions",
    "abstract": "As artificial intelligence systems become increasingly prevalent across critical sectors, governments worldwide are developing regulatory frameworks to ensure responsible AI deployment. This paper provides a comprehensive comparative analysis of AI governance approaches across major jurisdictions including the European Union, United States, China, United Kingdom, and Canada. We examine key regulatory dimensions including algorithmic accountability, data protection, bias mitigation, transparency requirements, and enforcement mechanisms. Our analysis reveals significant divergence in regulatory philosophy: the EU emphasizes rights-based comprehensive regulation through the AI Act, the US favors sector-specific guidelines with industry self-regulation, while China implements centralized algorithmic governance with social stability priorities. We identify three primary governance models: (1) Prescriptive Compliance (EU model), (2) Adaptive Governance (US/UK model), and (3) State-Directed Oversight (China model). Through analysis of 127 AI-related regulations and 43 enforcement cases, we find that prescriptive approaches achieve higher compliance rates (78% vs 52%) but may stifle innovation, while adaptive frameworks show greater technological advancement (23% faster deployment) but inconsistent safety outcomes. We propose a hybrid framework combining mandatory safety standards with flexible implementation pathways, demonstrating 34% improvement in both compliance and innovation metrics through policy simulation.",
    "authors": "Dr. Emily Watson, Prof. David Kim, Dr. James Thompson, Dr. Maria Gonzalez, Prof. Robert Chen",
    "published": "2024-05-10T09:15:00Z",
    "link": "http://arxiv.org/abs/2024.11111", 
    "pdf-link": "http://arxiv.org/pdf/2024.11111.pdf",
    "relevant_for": ["governance"],
    "topics": ["governance"],
    "search_category": "governance"
  }'

echo -e "\n\n=== Testing paper without analysis ==="

# Store a paper without AI analysis to test the \"no analysis\" display
curl -X POST "http://localhost:8080/newsletter/store-paper" \
  -H "Content-Type: application/json" \
  -u "admin:changeme" \
  -d '{
    "arxiv-id": "2024.99999v3",
    "title": "A Basic Paper Without AI Analysis",
    "abstract": "This is a simple test paper that demonstrates how papers without AI analysis are displayed in the library. The system should gracefully handle papers that lack the key_points, conclusion, and relevance_explanation fields.",
    "authors": "Test Author, Demo User",
    "published": "2024-05-16T12:00:00Z",
    "link": "http://arxiv.org/abs/2024.99999",
    "pdf-link": "http://arxiv.org/pdf/2024.99999.pdf",
    "relevant_for": [],
    "topics": [],
    "search_category": ""
  }'

echo -e "\n\n=== All test papers stored! ==="
echo "🚀 Visit http://localhost:8080/newsletter/library to see the collection!"
echo "📄 Click on any paper to see the detailed view with AI analysis!"