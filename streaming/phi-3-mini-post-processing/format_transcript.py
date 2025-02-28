#!/usr/bin/env python3
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def format_transcript(input_file, output_file):
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    model_id = "microsoft/Phi-3-mini-4k-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # Load model with 8-bit quantization for memory efficiency
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,  # Use float16 for efficiency
        device_map="auto",          # Automatically use GPU if available
        load_in_8bit=True           # 8-bit quantization to reduce memory usage
    )
    
    # Read the transcription
    with open(input_file, 'r') as f:
        transcript = f.read()
    
    # Create prompt for formatting
    prompt = f"""<|user|>
Please format this transcript with proper capitalization, paragraphs, and punctuation. 
Maintain the meaning but improve readability by:
1. Breaking into logical paragraphs
2. Fixing capitalization
3. Adding proper punctuation
4. Removing filler words and false starts when appropriate

Here's the transcript:
{transcript}
<|assistant|>"""
    
    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate output
    print("Formatting transcript...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.1,
            do_sample=False
        )
    
    # Decode the output
    result = tokenizer.decode(outputs[0], skip_special_tokens=False)
    
    # Clean up the response to extract just the formatted transcript
    if "<|assistant|>" in result:
        formatted_text = result.split("<|assistant|>")[1].strip()
        if "<|user|>" in formatted_text:
            formatted_text = formatted_text.split("<|user|>")[0].strip()
    else:
        formatted_text = result
    
    # Write the formatted transcript
    with open(output_file, 'w') as f:
        f.write(formatted_text)
    
    print(f"Formatted transcript saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python format_transcript.py <input_file> <output_file>")
        sys.exit(1)
    
    format_transcript(sys.argv[1], sys.argv[2])
