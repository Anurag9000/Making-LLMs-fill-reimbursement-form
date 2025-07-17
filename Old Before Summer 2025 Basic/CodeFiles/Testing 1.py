# Optional: For better acceleration (especially in multi-image or video scenarios),
# you can enable flash_attention_2 by uncommenting the following block:
# model = Qwen2VLForConditionalGeneration.from_pretrained(
#     "prithivMLmods/LatexMind-2B-Codec",
#     torch_dtype=torch.bfloat16,
#     attn_implementation="flash_attention_2",
#     device_map="auto",
# )

# Optionally, you can adjust the number of visual tokens by setting min_pixels and max_pixels.
# For example:
# min_pixels = 256 * 28 * 28
# max_pixels = 1280 * 28 * 28
# processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct", min_pixels=min_pixels, max_pixels=max_pixels)

import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# 1. Load the model
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "prithivMLmods/LatexMind-2B-Codec",
    torch_dtype="auto",
    device_map="auto"
)

# 2. Load the processor
processor = AutoProcessor.from_pretrained("prithivMLmods/Qwen2-VL-OCR-2B-Instruct")

# Path to the folder containing your images (named 1.png, 2.png, 3.png, etc.)
image_folder = "images"

# 3. Sort image files in numeric order
#    This assumes your files are named "1.png", "2.png", ... "n.png"
image_files = sorted(
    os.listdir(image_folder),
    key=lambda x: int(os.path.splitext(x)[0])
)

all_latex_outputs = []

for image_file in image_files:
    # 4. Build the path to the image
    image_path = os.path.join(image_folder, image_file)
    
    # 5. Define the conversation/message
    #    You can change the prompt text as needed.
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": "Please convert this document screenshot to LaTeX code."}
            ],
        }
    ]

    # 6. Convert the conversation to the model’s chat template
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # 7. Extract the images (and/or videos) for the model
    image_inputs, video_inputs = process_vision_info(messages)

    # 8. Prepare the model inputs
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda" if torch.cuda.is_available() else "cpu")

    # 9. Generate the LaTeX code
    generated_ids = model.generate(**inputs, max_new_tokens=1024)

    # 10. Remove the prompt portion from the output
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    # 11. Decode the tokens to text
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )

    # `output_text` is a list with a single string; grab the string
    latex_code = output_text[0]

    # 12. Collect LaTeX from each image
    all_latex_outputs.append(latex_code)

# 13. Write the combined LaTeX code to output.txt
with open("output.txt", "w", encoding="utf-8") as f:
    for latex_code in all_latex_outputs:
        f.write(latex_code + "\n\n")
