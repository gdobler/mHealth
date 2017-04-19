## 0

copy `/share/apps/faster-rcnn-pytorch/20170308/intel` to your own folder `/home/netID` or `/scratch/netID`

```shell
module load faster-rcnn-pytorch/intel/20170308
```
```shell
srun --x11 --mem=4000 -p gpu --gres=gpu:k80:1 --pty /bin/bash
# srun --x11 --mem=4000 -p gpu --gres=gpu:p1080:1 --pty /bin/bash
```

Follow the instruction [here](https://github.com/djfan/faster_rcnn_pytorch/blob/master/README.md) 



## 1

If use gpu k80, change the scripts in `intel/faster_rcnn_pytorch/faster_rcnn/faster_rcnn.py`

```python
from roi_pooling.modules.roi_pool_py import RoIPool
# from roi_pooling.modules.roi_pool import RoIPool
```

If use original `VOC2007` dataset to run testing or training before, remove cache files `.pkl` in `VOCdevkit/annotations_cache/` and `/intel/data/cache/` 



## 2

Create a new directory `VOC2007` for your customized image dataset (see below), then replace old `VOC2007` with new one.

```
# not seperate train and val set yet in this example.
.
├── Annotations
│   ├── 11228.xml
│   └── 11955.xml
├── ImageSets
│   └── Main
│       ├── cigar_test.txt
│       ├── cigar_trainval.txt
│       ├── test.txt
│       └── trainval.txt
└── JPEGImages
    ├── 11228.jpg
    └── 11955.jpg
```

`JPEGImages` contains all streetmap images fetch from google in `.jpg` format.

`Annotations` contains information for each image in `.xml` format. One `xml` file is corresponding to one street image. 

```xml
<annotation>
	<folder>VOC2007</folder>
	<filename>11228.jpg</filename>
	<source>
		<database>The VOC2007 Database</database>
		<annotation>PASCAL VOC2007</annotation>
		<image>flickr</image>
		<flickrid>329145082</flickrid>
	</source>
	<owner>
		<flickrid>hiromori2</flickrid>
		<name>Hiroyuki Mori</name>
	</owner>
	<size>
		<width>640</width>
		<height>480</height>
		<depth>3</depth>
	</size>
	<segmented>0</segmented>
	<object>
		<name>cigar</name>
		<pose>Unspecified</pose>
		<truncated>0</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>378</xmin>
			<ymin>285</ymin>
			<xmax>444</xmax>
			<ymax>384</ymax>
		</bndbox>
	</object>
	<object>
		<name>cigar</name>
		<pose>Unspecified</pose>
		<truncated>0</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>380</xmin>
			<ymin>285</ymin>
			<xmax>443</xmax>
			<ymax>362</ymax>
		</bndbox>
	</object>
</annotation>
```

If there are multiple traget pitches in one single street image, there will be multiple `<object>` sections in the file. For now, we need to customize `filename` `size` `name` `bndbox` for our own images. Others like `truncated` `difficult` may be customized in the future. For negative examples, leave the contents of these sections empty.  [devkit doc](http://host.robots.ox.ac.uk/pascal/VOC/voc2007/devkit_doc_07-Jun-2007.pdf)

`ImageSets` For image detection, only keep `Main` folder. The final version `Main` shoule be like:

```
.
├── cigar_test.txt
├── cigar_train.txt
├── cigar_trainval.txt
├── cigar_val.txt
├── test.txt
├── train.txt
├── trainval.txt
└── val.txt
```

`tranval` is a combination of `train` and `val`. 

Each `cigar_*.txt` has two columns, image ID (filenames without `.jpg`) and label (1 or -1)

`test.txt` `train.txt` `val.txt` and `trainval.txt` only contains one column, image ID.

(note: in original `VOC2007/ImageSets/Main/`, don't be confussed with `train_train.txt` and `train.txt`)

Now, the customized image dataset is ready.



## 3

The detection result of `test.py` will be store in `/intel/data/VOCdevkit2007/results/VOC2007/Main/comp4_det_test_cigar.txt` 



## 4

Next step, change some lines of code in original scripts. 

```
cd intel
```

1. `train.py`


```python
use_tensorboard = False

end_step = 5 # How many steps in training process? 

if (step %2 == 0) and step > 0: # save the intermediate model after every 2 steps training.
```

2. `test.py` 

```python
trained_model = 'models/saved_model_k80/faster_rcnn_4.h5'

thresh = 0.8
test_net(save_name, net, imdb, max_per_image, thresh=thresh, vis=vis)
# If the probability of detected object is higher than thresh, its bbox will be shown up. 
```

3.  `demo.py`


```python
model_file = 'models/saved_model_k80/faster_rcnn_4.h5'

dets, scores, classes = detector.detect(image, 0.85) 
# change the threshold value if necessary.
```

4.  `experiments/cfgs/faster_rcnn_end2end.yml`


```yaml
# NCLASSES: 21 
NCLASSES: 2
```

5. `/faster_rcnn/datasets/pascal_voc.py`

```python
# self._classes = ('__background__',  # always index 0
        #                 'aeroplane', 'bicycle', 'bird', 'boat',
        #                 'bottle', 'bus', 'car', 'cat', 'chair',
        #                 'cow', 'diningtable', 'dog', 'horse',
        #                 'motorbike', 'person', 'pottedplant',
        #                 'sheep', 'sofa', 'train', 'tvmonitor')        
self._classes = ('__background__', 'cigar')

```

6. `/faster_rcnn/faster_rcnn.py`

```python
class FasterRCNN(nn.Module):
	n_classes = 2
    # n_classes = 21
    classes = np.asarray(['__background__','cigar'])
    # classes = np.asarray(['__background__',
    #                   'aeroplane', 'bicycle', 'bird', 'boat',
    #                   'bottle', 'bus', 'car', 'cat', 'chair',
    #                   'cow', 'diningtable', 'dog', 'horse',
    #                   'motorbike', 'person', 'pottedplant',
    #                   'sheep', 'sofa', 'train', 'tvmonitor'])

```



## 5

**Note**

1. resizing scripts in `faster_rcnn_pytorch` :  `/faster_rcnn/fast_rcnn/bbox_transform.py`



**To-Do**

- [ ] `.xml` for 300+ streetmap images with signs and other 'noise' streetmap images.
- [ ] Image manipulation for all streetmap images mentioned above by Mona's code.
- [ ] Seperate data into test/train/val sets, then tune hyper-parameters.
- [ ] If necessay, change the structure of cnn (e.g. `vgg16.py`) and tune the loss function in `faster_rcnn.py`