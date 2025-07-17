import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# Load the non-GGUF model that is directly supported
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "prithivMLmods/LatexMind-2B-Codec",
    torch_dtype="auto",
    device_map="auto"
)

processor = AutoProcessor.from_pretrained("prithivMLmods/Qwen2-VL-OCR-2B-Instruct")

# The rest of your code remains the same...


# 3. Folder containing images (e.g., 1.png, 2.jpg, etc.)
image_folder = "images"

# 4. Gather and sort image files numerically by filename (adjust extensions as needed)
image_files = sorted(
    [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
    key=lambda x: int(os.path.splitext(x)[0])
)

all_latex_outputs = []

for image_file in image_files:
    # 5. Construct full path to the image file
    image_path = os.path.join(image_folder, image_file)
    
    # 6. Create a message with the image and the text instruction
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": "Please convert this document screenshot to LaTeX code."}
            ]
        }
    ]
    
    # 7. Prepare the text prompt using the processor's chat template
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # 8. Process visual inputs from the messages (extract images/videos)
    image_inputs, video_inputs = process_vision_info(messages)
    
    # 9. Prepare the model inputs (tokenize text and process images)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = inputs.to(device)
    
    # 10. Generate LaTeX code (tweak max_new_tokens if you need longer/shorter outputs)
    generated_ids = model.generate(**inputs, max_new_tokens=512)
    
    # 11. Trim out the prompt tokens so that only new tokens remain
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    
    # 12. Decode the generated token IDs to obtain LaTeX text
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )
    
    # output_text is a list (one per input); here we take the first element
    latex_code = output_text[0]
    all_latex_outputs.append(latex_code)

# 13. Write the combined LaTeX code for all images to output.txt
with open("output.txt", "w", encoding="utf-8") as f:
    for code in all_latex_outputs:
        f.write(code + "\n\n")

print("LaTeX conversion complete! Combined output written to output.txt")
