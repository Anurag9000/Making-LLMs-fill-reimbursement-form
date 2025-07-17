import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# 1. Load the Qwen2-VL-7B-Latex-OCR model
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "erickrus/Qwen2-VL-7B-Latex-OCR",
    torch_dtype="auto",
    device_map="auto"
)

# 2. Load the corresponding processor
processor = AutoProcessor.from_pretrained("erickrus/Qwen2-VL-7B-Latex-OCR")

# 3. Folder containing your images (named 1.png, 2.png, 3.png, ...)
image_folder = "images"

# 4. Sort image files in numeric order (assuming filenames are "1.png", "2.jpg", etc.)
image_files = sorted(
    [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
    key=lambda x: int(os.path.splitext(x)[0])
)

all_latex_outputs = []

for image_file in image_files:
    # 5. Build the path to the image
    image_path = os.path.join(image_folder, image_file)

    # 6. Define the conversation/message
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": "Please convert this document screenshot to LaTeX code."}
            ],
        }
    ]

    # 7. Convert the conversation to the model’s chat template
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # 8. Extract the images (and/or videos) for the model
    image_inputs, video_inputs = process_vision_info(messages)

    # 9. Prepare the model inputs
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = inputs.to(device)

    # 10. Generate the LaTeX code (tweak max_new_tokens if needed)
    generated_ids = model.generate(**inputs, max_new_tokens=512)

    # 11. Remove the prompt portion from the output
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    # 12. Decode the tokens to text
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )

    # `output_text` is a list with a single string; extract it
    latex_code = output_text[0]

    # 13. Collect LaTeX from each image
    all_latex_outputs.append(latex_code)

# 14. Write the combined LaTeX code to output.txt
with open("output.txt", "w", encoding="utf-8") as f:
    for latex_code in all_latex_outputs:
        f.write(latex_code + "\n\n")

print("LaTeX conversion complete! See output.txt for the results.")
