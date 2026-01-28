import os
import shutil
import gc
import argparse
from ultralytics import YOLO

def run_inference(images_dir, model_path, gpu_id):
    # Load model
    model = YOLO(model_path)

    # Derive model name without extension for output naming
    model_name = os.path.splitext(os.path.basename(model_path))[0]
    # Output base directory: same parent as images_dir, named test_<model_name>
    parent_dir = os.path.dirname(images_dir.rstrip(os.sep)) or os.getcwd()
    output_base_dir = os.path.join(parent_dir, f"test_{model_name}")

    images_out = os.path.join(output_base_dir, 'images')
    labels_out = os.path.join(output_base_dir, 'ai_labels')
    os.makedirs(images_out, exist_ok=True)
    os.makedirs(labels_out, exist_ok=True)

    # Find all image files in images_dir (non-recursive)
    img_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
    image_files = [f for f in os.listdir(images_dir)
                   if os.path.splitext(f)[1].lower() in img_extensions]
    if not image_files:
        print(f"No images found in {images_dir}")
        return

    print(f"Running YOLO inference on {len(image_files)} images in {images_dir}")

    # Run inference
    results = model(os.path.join(images_dir, '*'),
                    batch=40,
                    device=gpu_id,
                    conf= 0.25, #0.001, pothole [YD] #0.25 YD, HS, GM, CN
                    iou=0.5,
                    classes=[0],
                    #save_txt=True,
                    show=True,
                    save=True,
                    show_labels=True
                    )

    # Organize outputs
    # for res in results:
    #     orig_path = res.path
    #     filename = os.path.basename(orig_path)
    #     name_wo_ext = os.path.splitext(filename)[0]
    #     txt_name = f"{name_wo_ext}.txt"
    #     default_labels_dir = os.path.join(res.save_dir, 'labels')
    #     txt_src = os.path.join(default_labels_dir, txt_name)

    #     # Only copy images if label exists
    #     if os.path.exists(txt_src):
    #         shutil.copy2(orig_path, os.path.join(images_out, filename))
    #         shutil.move(txt_src, os.path.join(labels_out, txt_name))

    # # Cleanup
    # shutil.rmtree(results[0].save_dir, ignore_errors=True)
    # gc.collect()
    # print(f"Results saved to {output_base_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch YOLO inference for a directory of images.')
    parser.add_argument('--images_dir', required=True, help='Path to directory containing images')
    parser.add_argument('--model_path', required=True, help='Path to YOLO model .pt file')
    parser.add_argument('--gpu_id', type=int, default=0, help='GPU device ID to run inference on')
    args = parser.parse_args()

    run_inference(args.images_dir, args.model_path, args.gpu_id)
