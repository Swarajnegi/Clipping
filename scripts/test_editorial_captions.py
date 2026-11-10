"""Schema checks for synchronized depth captions and legacy specifications."""
import copy
import unittest
from build import validate_reference_edit


class EditorialChecks(unittest.TestCase):
    def setUp(self):
        self.edit = {'profile':'editorial','layers':[{'t':0,'dur':1,'text':'a word',
          'x':100,'y':500,'size':90,'font':'inter','wordTimes':[0,0.4],'depth':'behind'}],
          'foregroundMasks':[{'t':0,'dur':1,'keyframes':[
          {'t':0,'points':[[10,10],[100,10],[100,100]]},
          {'t':1,'points':[[20,10],[110,10],[110,100]]}]}]}

    def test_valid_depth_composition(self):
        validate_reference_edit(self.edit, 1)

    def test_true_italic_faces_and_legacy_upright(self):
        self.edit['layers'][0]['italic'] = True
        validate_reference_edit(self.edit, 1)
        self.edit['layers'][0].update(font='cormorant', weight=700)
        validate_reference_edit(self.edit, 1)
        for change in ({'italic': False}, {'weight': 800}, {'italic': 'yes'}):
            edit = copy.deepcopy(self.edit)
            edit['layers'][0].update(change)
            with self.assertRaises(ValueError): validate_reference_edit(edit, 1)
        self.edit['layers'][0].update(font='inter', italic=False, weight=800)
        validate_reference_edit(self.edit, 1)

    def test_depth_requires_full_mask_coverage(self):
        self.edit['foregroundMasks'][0]['dur']=0.8
        self.edit['foregroundMasks'][0]['keyframes'][-1]['t']=0.8
        with self.assertRaisesRegex(ValueError,'covering'):
            validate_reference_edit(self.edit,1)

    def test_mask_cannot_morph_between_different_vertex_counts(self):
        self.edit['foregroundMasks'][0]['keyframes'][-1]['points'].pop()
        with self.assertRaisesRegex(ValueError,'vertex count'):
            validate_reference_edit(self.edit,1)

    def test_mask_times_are_strict_and_coordinates_are_finite(self):
        for value in (float('nan'),-1,1200):
            edit=copy.deepcopy(self.edit)
            edit['foregroundMasks'][0]['keyframes'][0]['points'][0][0]=value
            with self.assertRaises(ValueError): validate_reference_edit(edit,1)
        self.edit['foregroundMasks'][0]['keyframes'][-1]['t']=0
        with self.assertRaisesRegex(ValueError,'strictly ordered'):
            validate_reference_edit(self.edit,1)

    def test_word_alignment_and_motion_bounds(self):
        self.edit['layers'][0]['wordTimes']=[0.8,0.2]
        with self.assertRaisesRegex(ValueError,'word times'):
            validate_reference_edit(self.edit,1)
        self.edit['layers'][0]['wordTimes']=[0,0.4]
        self.edit['layers'][0]['motion']={'inSec':float('nan')}
        with self.assertRaisesRegex(ValueError,'motion'):
            validate_reference_edit(self.edit,1)

    def test_existing_authored_styles_still_validate(self):
        for profile in ('restrained','kinetic'):
            validate_reference_edit({'profile':profile,'layers':[{'t':0,'dur':1,
              'text':'hello','x':100,'y':500,'size':62,'font':'sans','italic':True}]},1)

    def test_invalid_shadow_is_not_silently_ignored(self):
        self.edit['layers'][0]['shadow']='invisible'
        with self.assertRaisesRegex(ValueError,'shadow'):
            validate_reference_edit(self.edit,1)

    def test_difference_surface_and_opacity_bounds(self):
        self.edit['layers'][0].update(surface='difference',fillOpacity=0.8)
        validate_reference_edit(self.edit,1)
        for opacity in (float('nan'),-0.1,1.1):
            self.edit['layers'][0]['fillOpacity']=opacity
            with self.assertRaisesRegex(ValueError,'fillOpacity'):
                validate_reference_edit(self.edit,1)

if __name__=='__main__': unittest.main()
