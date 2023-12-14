import { useState } from "react";
import { Dropdown } from "react-native-element-dropdown";

type DropDownSelectionProps = {
  values: object[],
  defaultValue: object
  setSelection?: (value : any) => void,
  width?: number
};

export default function DropDownSelection(props : DropDownSelectionProps) {
  const [valueSelected, setValueSelected] = useState(props.defaultValue);
  const width = (props.width)?props.width:80;

  return (
    <Dropdown
      placeholderStyle={{
        backgroundColor: 'none',
        borderWidth: 0,
        elevation: 0,
        shadowOpacity: 0,
        color: '#E8E3E3',
        height: 20, 
      }}
      selectedTextStyle={{
        fontSize: 14,
        backgroundColor: 'none',
        color: '#E8E3E3',
        height: 20, 
      }}
      itemContainerStyle={{
        flexShrink: 1,
        backgroundColor: '#23232D',
        borderWidth: 0,
        elevation: 0,
        shadowOpacity: 0,
        alignItems: 'center',
        // height: 40,
        alignContent: 'center', 
        paddingVertical: 0,
      }}
      itemTextStyle={{
        // backgroundColor: '#FF0000',
        fontFamily: 'Inter-Regular',
        color: '#E8E3E3',
        borderWidth: 0,
        elevation: 0,
        shadowOpacity: 0,
        paddingTop: 0,
        paddingBottom: 0,
      }}
      selectedStyle={{
        backgroundColor: 'none',
        borderWidth: 0,
        elevation: 0,
        shadowOpacity: 0,
        height: 20, 
      }}
      containerStyle={{
        // backgroundColor: '#0000FF',
        borderWidth: 0,
        // borderColor: '#0000FF'
        elevation: 0,
        shadowOpacity: 0,
        paddingVertical: 0,
        // height: 80, 
      }}
      iconStyle={{
        width: 20,
        height: 20,
      }}
      fontFamily="Inter-Regular"
      activeColor="#39393C"
      maxHeight={300}
      labelField={"label"}
      valueField={"value"}
      // placeholder={!isFocus ? 'Select item' : '...'}
      value={valueSelected}
      // onFocus={() => setIsFocus(true)}
      // onBlur={() => setIsFocus(false)}
      onChange={item => {
        setValueSelected(item);
        if (props.setSelection) { props.setSelection(item); }
        // setCollectionOwner(item);
        // setIsFocus(false);
      }}
      data={props.values}
      style={{
        margin: 16,
        // height: 50,
        width: width,
        backgroundColor: 'none',
        // borderRadius: 12,
        // padding: 12,
        // shadowOpacity: 0.2,
        // shadowRadius: 1.41,
  
        // elevation: 2,
      }}
      placeholder={"None Selected"}
    />
  );
}