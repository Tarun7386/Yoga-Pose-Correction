import os
import requests

def download_images_from_txt(txt_path, output_folder):
    pose_name = os.path.splitext(os.path.basename(txt_path))[0]
    pose_folder = os.path.join(output_folder, pose_name)

    os.makedirs(pose_folder, exist_ok=True)

    with open(txt_path, 'r') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        parts = line.strip().split('\t')
        if len(parts) != 2:
            continue  # skip bad lines

        filename, url = parts
        save_path = os.path.join(pose_folder, os.path.basename(filename))

        try:
            response = requests.get(url, timeout=10)
            with open(save_path, 'wb') as img_file:
                img_file.write(response.content)
            print(f"✅ Downloaded: {save_path}")
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

if __name__ == '__main__':
    dataset_dir = 'dataset'  # folder with .txt files
    txt_files = [f for f in os.listdir(dataset_dir) if f.endswith('.txt')]

    for txt_file in txt_files:
        txt_path = os.path.join(dataset_dir, txt_file)
        download_images_from_txt(txt_path, dataset_dir)
